import subprocess
import botocore
import boto3
import hashlib
import json

class EC2Manager(object):
    def __init__(self, aws_region = None, aws_profile = None):
        self._created_instances = []
        self._policies = None
        self._session = None
        self._aws_profile = aws_profile
        self._aws_region = aws_region
        self._ec2_client = self._get_client('ec2')
        self._iam_client = self._get_client('iam')
        self._sts_client = self._get_client('sts')
        self._account_id = None

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
    
    def _load_policy_file(self, name):
        policy_str = None
        with open(name + ".policy") as f:
            policy_str = f.read()
        return policy_str

    def _get_account_id(self):
        if self._account_id is None:
            self._account_id = self._sts_client.get_caller_identity().get('Account')
        return self._account_id

    def _get_policies(self):
        """
        Retrieve all IAM policies for this account, caching them
        """
        if self._policies is not None:
            return self._policies
        policies = self._iam_client.list_policies(
            Scope='All',
            PathPrefix='/RedLeader/'
        )['Policies']
        self._policies = policies
        return self._policies

    def _policy_name(self, service):
        params = json.dumps(service['params'], sort_keys=True)
        h = hashlib.md5()
        h.update(params.encode('utf-8'))
        hash_str = str(h.hexdigest())
        return "RedLeader-EC2-%s-%s-Policy" % (service['name'], hash_str)
    
    def _create_iam_policy(self, service):
        template = self._load_policy_file(service['name'])
        policy = template

        for param in service['params']:
            policy = policy.replace("{%s}" % param, service['params'][param])

        builtin_params = {
            "account_id": self._get_account_id()
        }
        for param in builtin_params:
            policy = policy.replace("{%s}" % param, builtin_params[param])
            
        print(service)
        print("Creating policy %s with template: " % self._policy_name(service))
        print(policy)
        response = self._iam_client.create_policy(
            PolicyName=self._policy_name(service),
            Path="/redleader/",
            PolicyDocument=policy,
            Description='RedLeader policy for %s' % service
        )
        return response['Policy']['Arn']

    def _get_iam_policy(self, service):
        policies = self._get_policies()
        for policy in policies:
            if policy['PolicyName'] == self._policy_name(service):
                print("Found cached policy %s" % policy['PolicyName'])
                return policy['Arn']
        print("No policy found for service: ")
        print("\t %s" % str(service))
        return self._create_iam_policy(service)

    def create_iam_role(self, name, services):
        """
        Create an IAM role with access to the given services, permissions
        dictated by the default service policy templates
        """
        role_response = self._iam_client.create_role(
                RoleName=name,
                AssumeRolePolicyDocument=self._load_policy_file("assume_role")
        )
        for service in services:
            policy = self._get_iam_policy(service)
            response = self._iam_client.attach_role_policy(
                RoleName=name,
                PolicyArn=policy
            )
        return role_response

    def create_instance_profile(self, iam_role):
        pass

    def create_instance(self, image_id, key_name, startup_script, count,
                        instance_type, instance_profile):
        res = self._ec2_client.run_instances({
            ImageId: image_id,
            MinCount: count,
            MaxCount: count,
            KeyName: key_name,
            UserData: startup_script,
            IamInstanceProfile: {"Name": instance_profile},
            InstanceType: instance_type,
        })
        instance_ids = map(lambda x: x['InstanceId'], res['Instances'])
        self._created_instances.append(instance_ids)
        return instance_ids

    def terminate_instance(self, instance_id):
        return self._ec2_client.terminate_instances(InstanceIds = [instance_id])

ec2m = EC2Manager(aws_region="us-west-1",
                  aws_profile="john")
services = [
    {"name": "s3",
     "params": {"bucket_name": "my_bucket_name"}},
    {"name": "sqs",
     "params": {"queue_name": "my_queue_name"}}
]
role = ec2m.create_iam_role("some_role11", services)
