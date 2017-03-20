from redleader.resources import Resource
import random
import os.path
import pkg_resources
import json

class IAMInstanceProfileResource(Resource):
    """
    Create an IAM Instance Profile with access to the given resources.
    Automatically creates an IAMRoleResource if provided with resource list

    A list of ResourcePermissions can be provided, in which case an IAMRoleResource
    will be automatically generated. Otherwise, an IAMRoleResource can be provided directly.
    """

    def __init__(self, context, permissions=[], roles=[], services=['ec2.amazonaws.com']):
        super(IAMInstanceProfileResource, self).__init__(context, {})
        self._permissions = permissions
        self._generated_role = None
        self._roles = roles
        self._services = services

        for permission in self._permissions:
            self.add_dependency(permission.resource)

        if len(self._roles) is not 0:
            for role in self._roles:
                self.add_dependency(role)

    def _generate_sub_resources(self):
        self._generated_role = IAMRoleResource(self._context,
                                               self._permissions,
                                               services=self._services,
                                               policies=[]
        )
        self._roles.append(self._generated_role)
        self.add_dependency(self._generated_role)
        return [self._generated_role]

    def _cloud_formation_template(self):
        return {
            "Type": "AWS::IAM::InstanceProfile",
            "Properties": {
                "Path": "/redleader/",
                "Roles": [Resource.cf_ref(x) for x in self._roles]
            }
        }

class IAMRoleResource(Resource):
    """
    Create an IAM role with access to the given resources.
    `policies` should be a list of IAMPolicyResource objects
    """
    def __init__(self, context, permissions, services=[], policies=[], policy_arns=[]):
        super(IAMRoleResource, self).__init__(context, {})
        self._permissions = permissions
        self._services = services
        self._policies = policies
        self._generated_policy = None
        self._policy_arns = policy_arns

        for permission in self._permissions:
            self.add_dependency(permission.resource)

        for policy in self._policies:
            self.add_dependency(policy)

    @staticmethod
    def assumeRolePolicyDocument(services):
        return {
            "Version" : "2012-10-17",
            "Statement": [
                {
                    "Sid": "",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": services
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }

    def _cloud_formation_template(self):
        return {
            "Type": "AWS::IAM::Role",
            "Properties": {
                "AssumeRolePolicyDocument":
                   IAMRoleResource.assumeRolePolicyDocument(self._services),
                "ManagedPolicyArns": [Resource.cf_ref(x) for x in self._unique_policies()] +\
                  self._policy_arns,
                "Path": "/redleader/",
                "RoleName": self._id_placeholder()
            }
        }
        return "IAM Role template"

    def _unique_policies(self):
        keys = {}
        unique = []
        for policy in self._policies:
            if policy.get_id() not in keys:
                unique.append(policy)
                keys[policy.get_id()] = True
        return unique

    def _generate_sub_resources(self):
        """
        Generate a single sub-policy representing access to provided resources
        """
        if len(self._permissions) == 0:
            return []

        self._generated_policy = IAMPolicyResource(self._context, self._permissions)
        self._policies.append(self._generated_policy)
        #if len(self._policies) > 0 and self._generated_policy.get_id() == self._policies[0].get_id():
        #    return []
        self.add_dependency(self._generated_policy)
        return [self._generated_policy]

class IAMPolicyResource(Resource):
    def __init__(self, context, permissions):
        super(IAMPolicyResource, self).__init__(context, {})
        self._permissions = permissions

    def _cloud_formation_template(self):
        return {
            "Type" : "AWS::IAM::ManagedPolicy",
            "Properties" : {
                "Description" : self._id_placeholder(),
                "Path": "/redleader/",
                "PolicyDocument": generate_policy_document(
                    self._context, self._permissions)
            }
        }

def generate_policy_document(context, permissions):
    policy_statements = []
    for permission in permissions:
        resource = permission.resource
        # TODO: Differentiate between read, write, readwrite
        for service in resource.iam_service_policies():
            policy = create_iam_policy(context, service)
            policy_statements += policy
    return {
        "Version" : "2012-10-17",
        "Statement": policy_statements
    }

def load_policy_file(name):
    resource_package = __name__
    resource_path = '/'.join(('policies', '%s.policy' % name))
    return pkg_resources.resource_string(resource_package, resource_path).decode('utf-8')

def create_iam_policy(context, service):
    template = load_policy_file(service['name'])
    policy = template

    for param in service['params']:
        policy = policy.replace("{%s}" % param, service['params'][param])

    builtin_params = {
        "account_id": context.get_account_id(),
        "aws_region": context.get_region()
    }
    for param in builtin_params:
        policy = policy.replace("{%s}" % param, builtin_params[param])

    return json.loads(policy)
