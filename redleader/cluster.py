import json
import time

import botocore.exceptions

from redleader.resources import Resource
from redleader.exceptions import MissingDependencyError

class Cluster(object):
    def __init__(self, cluster_class, context):
        super()
        self._cluster_class = cluster_class
        self._context = context
        self._resources = {}

    def add_resource(self, resource):
        self._resources[resource.get_id()] = resource
        sub_resources = resource.generate_sub_resources()
        for sub_resource in sub_resources:
            self.add_resource(sub_resource)

    def validate(self):
        for resource_id in self._resources:
            resource = self._resources[resource_id]
            for dependency in resource.get_dependencies():
                if dependency.get_id() not in self._resources:
                    print("Missing dependency")
                    print(resource.get_id())
                    print(dependency.get_id())
                    print(self._resources.keys())
                    raise MissingDependencyError(
                        source_resource= resource.get_id(),
                        missing_resource= dependency.get_id()
                    )

    def cloud_formation_template(self):
        self.validate()
        templates = {}
        for resource_id in self._resources:
            resource = self._resources[resource_id]
            template = resource.cloud_formation_template()
            if template is not None:
                templates[resource_id] = template
        return {
               "AWSTemplateFormatVersion": "2010-09-09",
               "Resources": templates
        }

    def estimate_template_cost(self):
        template = self.cloud_formation_template()        
        client = self._context.get_client('cloudformation')
        return client.estimate_template_cost(TemplateBody=json.dumps(template))['Url']
        
    def deploy(self):
        client = self._context.get_client('cloudformation')
        return client.create_stack(
            StackName=self._cluster_class,
            TemplateBody=json.dumps(self.cloud_formation_template()),
            Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM']
        )

    def blocking_deploy(self, verbose=False):
        self.deploy()
        while self.deployment_status() == "CREATE_IN_PROGRESS":
            time.sleep(5)
            if verbose:
                print("Cluster creation in progress")
        if verbose:
            print("Cluster successfully created")
        return self.deployment_status()
            

    def deployment_status(self):
        client = self._context.get_client('cloudformation')
        response = client.describe_stacks(
                StackName=self._cluster_class
        )
        # Possible statuses:
        # 'StackStatus': 'CREATE_IN_PROGRESS'|'CREATE_FAILED'|'CREATE_COMPLETE'|'ROLLBACK_IN_PROGRESS'|'ROLLBACK_FAILED'|'ROLLBACK_COMPLETE'|'DELETE_IN_PROGRESS'|'DELETE_FAILED'|'DELETE_COMPLETE'|'UPDATE_IN_PROGRESS'|'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS'|'UPDATE_COMPLETE'|'UPDATE_ROLLBACK_IN_PROGRESS'|'UPDATE_ROLLBACK_FAILED'|'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS'|'UPDATE_ROLLBACK_COMPLETE'|'REVIEW_IN_PROGRESS',
        return response['Stacks'][0]['StackStatus']

    def delete(self):
        client = self._context.get_client('cloudformation')        
        return client.delete_stack(
            StackName=self._cluster_class
        )

    def blocking_delete(self, verbose=False):
        self.delete()
        try:        
            while self.deployment_status() == "DELETE_IN_PROGRESS":
                time.sleep(5)
                if verbose:
                    print("Cluster deletion in progress")
            if verbose:
                print("Cluster successfully deleted")
            return self.deployment_status()
        except botocore.exceptions.ClientError:
            if verbose:
                print("Stack fully deleted, could not obtain deployment status")
            return None
    
    def find_deployed_cluster(self):
        """
        Find resources for this cluster that have already deployed
        """
        raise NotImplementedError

    def cloud_formation_deploy(self):
        """
        TODO
        """
        raise NotImplementedError

class OfflineContext(object):
    def __init__(self, **kwargs):
        super()
        
    def get_session(self):
        raise OfflineContextError(action="get_session")

    def get_account_id(self):
        return "offline_context_account_id"

    def get_client(self):
        raise OfflineContextError(action="get_client")    
