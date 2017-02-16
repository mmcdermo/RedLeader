from .resource import Resource
from .ec2 import EC2InstanceResource
from .iam import IAMRoleResource, IAMInstanceProfileResource
import pkg_resources

class CodeDeployEC2InstanceResource(EC2InstanceResource):
    """
    Creates an EC2 server resource with the code deploy agent running.
    Takes the same keyword parameters as EC2InstanceResource.

    Automatically generates and depends upon a CodeDeployServiceRole.
    """

    def _get_init_script(self, region_name):
        resource_package = __name__
        resource_path = '/'.join(('scripts', 'code_deploy_init.sh'))
        s = pkg_resources.resource_string(resource_package, resource_path).decode('utf-8')
        s = s.replace("{region_name}", region_name)
        return s

    def generate_sub_resources(self):
        res = super().generate_sub_resources()
        if self._service_role is None:
            self._service_role = CodeDeployServiceRoleResource(self._context)
            self.add_dependency(self._service_role)

        res.append(self._service_role)
        res.append(self._instance_profile)
        self.add_dependency(self._instance_profile)
        return res

    def __init__(self, context, deployment_group, **kwargs):
        self._deployment_group = deployment_group
        self._service_role = None
        kwargs = self.configure_kwargs(context, kwargs)

        super().__init__(context, **kwargs)
        self.add_dependency(self._deployment_group)

    def configure_kwargs(self, context, kwargs):
        """
        Configure tags, init_script, and roles for code deploy
        """
        region_name = "us-west-1"
        if "region_name" in kwargs:
            region_name = kwargs[region_name]

        kwargs['tags'] = [self._deployment_group.get_ec2_tag()]
        kwargs['init_script'] = self._get_init_script(region_name)

        # Setup instance profile
        permissions = kwargs.get('permissions', [])
        roles = kwargs.get('roles', [])
        services = kwargs.get('services', []) +\
                   ['ec2.amazonaws.com', 'codedeploy.amazonaws.com']
        #roles.append(CodeDeployServiceRoleResource.global_service_role(context))

        self._instance_profile = IAMInstanceProfileResource(
            context,
            permissions=permissions,
            roles=roles,
            services=services
        )
        kwargs['instance_profile'] = self._instance_profile
        return kwargs

class CodeDeployServiceRoleResource(IAMRoleResource):
    def __init__(self, context, permissions=[], policies=[], policy_arns=[]):
        services = ['ec2.amazonaws.com', 'codedeploy.amazonaws.com']
        super().__init__(context,
                         permissions=permissions,
                         services=services,
                         policies=policies,
                         policy_arns = policy_arns +\
                           ["arn:aws:iam::aws:policy/service-role/AWSCodeDeployRole"]
        )

class CodeDeployDeploymentGroupResource(Resource):
    def __init__(self, context, application_name,
                 deployment_group_name=None, cf_params={}):
        super().__init__(context, cf_params)
        self._application_name = application_name
        self._application = None
        self._service_role = CodeDeployServiceRoleResource(self._context)
        self.add_dependency(self._service_role)
        self._ec2_tag_filters = [
            {"Key": "redleaderDeploymentGroup",
             "Type": "KEY_AND_VALUE",
             "Value": self._id_placeholder()
            }
        ]

        if deployment_group_name is None:
            self._deployment_group_name = self._id_placeholder()
        else:
            self._deployment_group_name = deployment_group_name

    def get_ec2_tag(self):
        return {"Key": "redleaderDeploymentGroup", "Value": self.get_id()}

    def generate_sub_resources(self):
        res = super().generate_sub_resources()
        res.append(self._service_role)

        if self._application is None:
            self._application = CodeDeployApplicationResource(
                self._context, self._application_name)
            self.add_dependency(self._application)
        res.append(self._application)
        return res

    def _cloud_formation_template(self):
        return {
          "Type" : "AWS::CodeDeploy::DeploymentGroup",
          "Properties" : {
              "ApplicationName" : self._application_name,
              #"AutoScalingGroups" : [],
              #"Deployment" : Deployment,
              #"DeploymentConfigName" : String,
              "DeploymentGroupName": self._deployment_group_name,
              "Ec2TagFilters" : self._ec2_tag_filters,
              "ServiceRoleArn" : Resource.cf_attr(self._service_role, "Arn")
          }
        }

class CodeDeployApplicationResource(Resource):
    def __init__(self, context, application_name, cf_params={}):
        super().__init__(context, cf_params)
        self._application_name = application_name

    def _cloud_formation_template(self):
        return {
            "Type" : "AWS::CodeDeploy::Application",
            "Properties" : {
                "ApplicationName": self._application_name,

            }
        }
