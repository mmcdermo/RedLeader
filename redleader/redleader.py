import boto3
from base64 import b64decode
import json
import subprocess
import botocore


class RedLeader(object):
    """
    Class that manages ECS cluster creation, deployment, and updates
    """
    def __init__(self, 
                 cluster_prefix,
                 image_name,
                 aws_access_key_id=None,
                 aws_secret_access_key=None,
                 aws_profile=None,
                 aws_region="us-west-1"
    ):
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key
        self._aws_profile = aws_profile
        self._aws_region = aws_region        
        self._cluster_prefix = cluster_prefix
        self._image_name = image_name
        self._session = None
        self._ecs_client = self._get_client('ecs')
        
        print("Red Leader Initialized")

    def _get_client(self, service):
        """
        Return a client configured with current credentials and region
        """
        if self._session is None:
            try:
                self._session = boto3.Session(profile_name=self._aws_profile,
                                              region_name=self._aws_region
                )
            except botocore.exceptions.ProfileNotFound:
                self._session = boto3.Session(region_name=self._aws_region)
        return self._session.client(service)

    def _task_defn_family(self):
        """
        Returns the task definiton family we'll create and look for in our account
        """
        return self._cluster_prefix + "-task"

    def _get_cluster(self):
        """
        Returns the cluster ARN for the cluster matching the setup cluster prefix
        """

        clusters = self._ecs_client.list_clusters()
        if len(clusters) is 0:
            raise Exception("No clusters found in current region.")

        cluster_arn = None
        for possible_cluster_arn in clusters['clusterArns']:
            if self._cluster_prefix in possible_cluster_arn:
                cluster_arn = possible_cluster_arn
        if cluster_arn is None:
            raise Exception("No cluster found containing cluster prefix '%s'" % self._cluster_prefix)
        print("Found cluster %s" % cluster_arn)        
        return cluster_arn

    def _get_latest_task_definition(self, cluster_arn):
        """
        Retrieves the task definition with the largest revision number for
        a given cluster.
        """
        cluster_desc = self._ecs_client.describe_clusters(clusters=[cluster_arn])
        task_defns = self._ecs_client.list_task_definitions(familyPrefix=self._task_defn_family())
        task_defn_arns = task_defns['taskDefinitionArns']

        print("Found %d matching task definitions" % len(task_defn_arns))

        if len(task_defn_arns) is 0:
            raise Exception("No matching task definitions found in cluster '%s'" % cluster_arn)

        max_rev = 0
        task_defn = None
        for task_defn_arn in task_defn_arns:
            task_desc = self._ecs_client.describe_task_definition(
                taskDefinition=task_defn_arn)
            if task_desc['taskDefinition']['revision'] > max_rev:
                max_rev = task_desc['taskDefinition']['revision']
                task_defn = task_desc['taskDefinition']
    
        if task_defn is None:
            raise Exception("Couldn't sort task definitions by revision")
        print("Found latest task definition with revision %d" % max_rev)
        return task_defn

    def _update_container_definition_image_tag(self, cont_defn, new_tag):
        """
        Update a container definition's image to utilize a certain tag
        """
        # Update image property
        new_cont_defn = cont_defn
        # Strip out current revision tag if present
        image_arr = new_cont_defn['image'].split(":")
        if len(image_arr) > 1:
            image_arr = image_arr[:-1]
        new_cont_defn['image'] = ":".join(image_arr + [new_tag])
        return new_cont_defn

    def _get_default_service(self):
        """
        Return the default service based on self._cluster_prefix
        """
        cluster_arn = self._get_cluster()
        services = self._ecs_client.list_services(
            cluster = cluster_arn)
        if len(services['serviceArns']) < 1:
            print(services)
            raise Exception('No services found for cluster %s' % cluster_arn)
        return services['serviceArns'][0]
        
    def _update_service_container_definition(self, service_arn, task_role_arn, cont_defn):
        """
        Update the service's container definition by generating
        a new task definition and updating the service to use that definition
        """
        cluster_arn = self._get_cluster()
        res = self._ecs_client.register_task_definition(
            family = self._task_defn_family(),
            taskRoleArn = task_role_arn,
            containerDefinitions = [cont_defn]
        )
        new_task_defn_arn = res['taskDefinition']['taskDefinitionArn']

        res = self._ecs_client.update_service(
            service = service_arn,
            cluster = cluster_arn,
            taskDefinition = new_task_defn_arn
        )
        return res
        
        
    def update_default_service_image_tag(self, tag):
        """
        Update the default service's image tag to the given tag
        """
        cluster_arn = self._get_cluster()
        task_defn = self._get_latest_task_definition(cluster_arn)
        if len(task_defn['containerDefinitions']) < 1:
            raise Exception("Too few container definitions for task")
        cont_defn = task_defn['containerDefinitions'][0]
        new_cont_defn = self._update_container_definition_image_tag(cont_defn, tag)

        service_arn = self._get_default_service()
        res = self._update_service_container_definition(
            service_arn,
            task_defn['taskRoleArn'],
            new_cont_defn)
        print("Updated default service image tag to "+tag)

        return res

    def _ecr_get_docker_login(self):
        ecr_client = self._get_client('ecr')
        result = ecr_client.get_authorization_token()
        for auth in result['authorizationData']:
            auth_token = b64decode(auth['authorizationToken']).decode()
            username, password = auth_token.split(':')
            return {"username": username,
                    "password": password,
                    "proxyEndpoint": auth['proxyEndpoint']}

    def _ecr_push_build(self, container_name, filepath):
        """
        Build & push the latest docker build with the given name to ECR.

        Tags the current build with the latest git commit
        """
        
        version = subprocess.Popen("git rev-parse --short HEAD", shell=True,
                               stdout=subprocess.PIPE).stdout.read().decode('utf-8')
        version = "v_" + version.strip()
        print("Git repo version: "+version)
        print("Building docker container %s:%s located at %s" % (container_name, version, filepath))
        res = subprocess.Popen("docker build -t %s:%s %s" % (container_name, version, filepath),
                               shell=True,
                               stdout=subprocess.PIPE).stdout.read().decode('utf-8')
        print(res)
        
        res = subprocess.Popen("docker tag %s:%s %s:%s" % 
                               (container_name, version, self._image_name, version),
                               shell=True,
                               stdout=subprocess.PIPE).stdout.read().decode('utf-8')
        print(res)
        print("docker tag %s:%s %s:%s" % 
                               (container_name, version, self._image_name, version))

        docker_auth = self._ecr_get_docker_login()
        login_str = ('docker login -u %s -p %s -e none %s' %
                     (docker_auth['username'],
                      docker_auth['password'],
                      docker_auth['proxyEndpoint']))

        res = subprocess.Popen(login_str + 
                               ("&& docker push %s:%s" % (self._image_name, version)),
                               shell=True,
                               stdout=subprocess.PIPE).stdout.read().decode('utf-8')
        print(res)
        return version
