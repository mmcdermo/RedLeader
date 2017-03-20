import json
import time
import sys
import boto3
import urllib
import os.path

import botocore.exceptions

from .resources import Resource
from .exceptions import MissingDependencyError, OfflineContextError
import util

class Cluster(object):
    def __init__(self, cluster_class, context, pretty_names=True):
        self._cluster_class = cluster_class
        self._context = context
        self._resources = {}
        self._pretty_names = pretty_names

    def add_resource(self, resource):
        for sub_resource in resource.generate_sub_resources():
            self.add_resource(sub_resource)
        self._resources[resource.get_id()] = resource

    def validate(self):
        for resource_id in self._resources:
            resource = self._resources[resource_id]
            for dependency in resource.get_dependencies():
                x = dependency.get_id()
                if x not in self._resources:
                    print("Missing dependency")
                    print(resource.get_id())
                    print(x)
                    print(self._resources.keys())
                    raise MissingDependencyError(
                        source_resource= resource.get_id(),
                        missing_resource= dependency.get_id()
                    )

    def _mod_identifier(self, ident):
        """
        Add the cluster class onto the cloud formation identifier
        """
        return self._cluster_class + ident

    def _cluster_mod_identifiers(self, tmpl, replaceMap=None):
        """
        Modify all cloud formation identifiers so that they're unique to this cluster class
        """
        if replaceMap is None:
            replaceMap = {}
            for k in self._resources:
                replaceMap[k] = self._mod_identifier(k)

        if isinstance(tmpl, str):
            tmpl = util.multireplace(tmpl, replaceMap)
        elif isinstance(tmpl, dict):
            for k in tmpl:
                tmpl[k] = self._cluster_mod_identifiers(tmpl[k], replaceMap)
        elif isinstance(tmpl, list):
            for idx in range(len(tmpl)):
                tmpl[idx] = self._cluster_mod_identifiers(tmpl[idx], replaceMap)
        return tmpl

    def cloud_formation_template(self):
        self.validate()
        Resource.reset_multiplicity()
        templates = {}
        for resource_id in self._resources:
            resource = self._resources[resource_id]
            template = resource.cloud_formation_template()
            if template is not None:
                templates[self._mod_identifier(resource_id)] = \
                    self._cluster_mod_identifiers(template)
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
        if verbose:
            print("Cluster creation in progress")
        i = 0
        while self.deployment_status() == "CREATE_IN_PROGRESS":
            i = (i + 1)
            if verbose:
                util.print_progress(i)
            time.sleep(5)
        if verbose:
            print("Cluster successfully created")
        return self.deployment_status()


    def describe_stack(self):
        client = self._context.get_client('cloudformation')
        return client.describe_stacks(
                StackName=self._cluster_class
        )

    def describe_resources(self):
        client = self._context.get_client('cloudformation')
        return client.describe_stack_resources(
            StackName=self._cluster_class
        )

    def describe_resource(self, resource):
        client = self._context.get_client('cloudformation')
        return client.describe_stack_resource(
            StackName=self._cluster_class,
            LogicalResourceId=self._mod_identifier(resource.get_id())
        )


    def deployment_status(self):
        response = self.describe_stack()
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
            i = 0
            if verbose:
                print("Cluster deletion in progress")
            while self.deployment_status() == "DELETE_IN_PROGRESS":
                i += 1
                if verbose:
                    util.print_progress(i)
                time.sleep(5)
            if verbose:
                print("Cluster successfully deleted")
            return self.deployment_status()
        except botocore.exceptions.ClientError:
            if verbose:
                print("Stack fully deleted, could not obtain deployment status")
            return None

    def cluster_exists(self):
        """
        Find resources for this cluster that have already deployed
        """
        try:
            status = self.deployment_status()
            return True
        except Exception as e:
            print("Cluster may not exist. Encountered error %s" % e)
            return False

    def cloud_formation_deploy(self):
        """
        TODO
        """
        raise NotImplementedError

class Context(object):
    def __init__(self, **kwargs):
        self._dict = None
        return

    def get_dict(self):
        """ Returns an english dictionary. Useful for pretty hashing"""
        if self._dict is not None:
            return self._dict
        dict_path = "/tmp/redleader_dict.txt"
        if(os.path.isfile(dict_path)):
            with open(dict_path, 'r') as f:
                self._dict = f.read().split("\n")
        else:
            print("Downloading fresh redleader dictionary")
            url = "https://svnweb.freebsd.org/csrg/share/dict/words?view=co&content-type=text%2Fplain&revision=61569"
            openfun = None
            if hasattr(urllib, "request"):
                # Python 3.x
                openfun = urllib.request.urlopen
            else:
                # Python 2.x
                openfun = urllib.urlopen

            response = openfun(url)
            dict_text = response.read().decode('utf-8')
            with open(dict_path, 'w') as f:
                f.write(dict_text)
            self._dict = dict_text.split("\n")
        return self._dict

class OfflineContext(Context):
    def __init__(self, **kwargs):
        super().__init__()

    def pretty_names(self):
        return False

    def get_session(self):
        raise OfflineContextError(action="get_session")

    def get_account_id(self):
        return "offline_context_account_id"

    def get_region(self):
        return "us-west-1"

    def get_client(self, service):
        raise OfflineContextError(action="get_client")

class AWSContext(Context):
    """
    Context manager for RedLeader, managing AWS sessions and clients.
    """

    def __init__(self,
                 aws_profile=None,
                 aws_access_key_id=None,
                 aws_secret_access_key=None,
                 aws_region="us-west-1",
                 pretty_names=True
    ):
        super(AWSContext, self).__init__()
        self._aws_profile = aws_profile
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key
        self._aws_region = aws_region
        self._pretty_names = pretty_names
        self._clients = {}
        self._account_id = None

        try:
            self._session = boto3.Session(profile_name=self._aws_profile,
                                          region_name=self._aws_region)
        except botocore.exceptions.NoCredentialsError:
            self._session = boto3.Session(region_name=self._aws_region)

    def get_session(self):
        return self._session

    def get_region(self):
        return self._aws_region

    def get_account_id(self):
        if self._account_id is None:
            self._account_id = self.get_client('sts').get_caller_identity().get('Account')
        return self._account_id

    def pretty_names(self):
        return self._pretty_names

    def get_client(self, client_type):
        if client_type not in self._clients:
            self._clients[client_type] = self._session.client(client_type)
        return self._clients[client_type]
