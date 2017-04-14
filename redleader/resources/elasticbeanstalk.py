from redleader.resources import Resource
import redleader.exceptions as exceptions
import redleader.util as util
from redleader.resources.iam import *

solution_stacks = {
    "python_3_4": "64bit Amazon Linux 2016.09 v2.3.3 running Python 3.4",
    "python_2_7": "64bit Amazon Linux 2016.09 v2.3.3 running Python 2.7",
    "go_1_6_6": "64bit Amazon Linux 2016.09 v2.3.3 running Go 1.6",
    "docker": "64bit Amazon Linux 2016.09 v2.5.2 running Docker 1.12.6",
    "docker_go": "64bit Debian jessie v2.5.2 running Go 1.4 (Preconfigured - Docker)", # golang:1.4.2-onbuild
    "docker_multi": "64bit Amazon Linux 2016.09 v2.5.2 running Multi-container Docker 1.12.6 (Generic)"
}


"""
Managed policy: AWSElasticBeanstalkFullAccess
"""

class ElasticBeanstalkEnvResource(Resource):
    """
    Resource modeling an Elastic Beanstalk Environment
    """
    def __init__(self,
                 context,
                 application,
                 application_version,
                 configuration_template,
                 cname_prefix=None,
                 description="",
                 cf_params={}
    ):
        super().__init__(context, cf_params)
        self._application = application
        self._application_version = application_version
        self._configuration_template = configuration_template
        self._description = description
        self._cname_prefix = cname_prefix
        if self._cname_prefix is None:
            self._cname_prefix = self.get_id()

        self.add_dependency(application)
        self.add_dependency(application_version)
        self.add_dependency(configuration_template)

    def get_id(self):
        return "elasticBeanstalkEnv%s%s" %\
            (util.sanitize_name(self._application._name),
             util.sanitize_name(self._description[:10]))

    def _cloud_formation_template(self):
        """
        Get the cloud formation template for this resource
        """
        return {
            "Type": "AWS::ElasticBeanstalk::Environment",
            "Properties": {
                "ApplicationName": Resource.cf_ref(self._application),
                "Description": self._description,
                "CNAMEPrefix": self._cname_prefix,
                "TemplateName": Resource.cf_ref(self._configuration_template),
                "VersionLabel": Resource.cf_ref(self._application_version)
            }
        }

class ElasticBeanstalkAppVersionResource(Resource):
    """
    Resource modeling an Elastic Beanstalk Application Version
    """
    def __init__(self,
                 context,
                 application,
                 s3_bucket,
                 s3_key,
                 description = "",
                 cf_params={}
    ):
        super().__init__(context, cf_params)
        self._application = application
        self._description = description
        self._s3_bucket = s3_bucket
        self._s3_key = s3_key
        self.add_dependency(application)

    def get_id(self):
        return "elasticBeanstalkAppVersion%s%s" % \
            (util.sanitize_name(self._application._name),
             util.sanitize_name(self._description[:10]))

    def _cloud_formation_template(self):
        """
        Get the cloud formation template for this resource
        """
        return {
            "Type": "AWS::ElasticBeanstalk::ApplicationVersion",
            "Properties": {
                "ApplicationName": Resource.cf_ref(self._application),
                "Description": self._description,
                "SourceBundle": {
                    "S3Bucket": self._s3_bucket,
                    "S3Key": self._s3_key
                }
            }
        }


class ElasticBeanstalkAppResource(Resource):
    """
    Resource modeling an Elastic Beanstalk Application
    """
    def __init__(self,
                 context,
                 name,
                 cf_params={}
    ):
        super().__init__(context, cf_params)
        self._name = name

    def get_id(self):
        return "elasticBeanstalkApp%s" % \
            util.sanitize_name(self._name)

    def _cloud_formation_template(self):
        """
        Get the cloud formation template for this resource
        """
        return {
            "Type": "AWS::ElasticBeanstalk::Application",
            "Properties": {
                "ApplicationName": self._name
            }
        }


class ElasticBeanstalkInstanceProfile(IAMInstanceProfileResource):
    def __init__(self, context, permission_resources):
        services = ["elasticbeanstalk.amazonaws.com", "ec2.amazonaws.com"]
        policy_arn = "arn:aws:iam::aws:policy/AWSElasticBeanstalkFullAccess"
        eh_policy_arn = "arn:aws:iam::aws:policy/service-role/AWSElasticBeanstalkEnhancedHealth"
        self._ebs_role = IAMRoleResource(context,
                                         permission_resources,
                                         services=services,
                                         policy_arns=[policy_arn, eh_policy_arn])
        super().__init__(
            context,
            permissions=permission_resources,
            roles=[self._ebs_role],
            services=services
        )
        self.add_dependency(self._ebs_role)

    def generate_sub_resources(self):
        return [self._ebs_role]

class ElasticBeanstalkConfigTemplateResource(Resource):
    """
    Resource modeling an Elastic Beanstalk Configuration Template

    Options are provided in the format:
    options = {
         "Namespace": {
            "OptionName": "Value"
         }
    }
    e.g.)
    options = {
        "aws:autoscaling:asg": {
           "MinSize": "2",
           "MaxSize": "6"
        },
        "aws:elasticbeanstalk:environment": {
           "EnvironmentType": "LoadBalanced"
        }
    }

    `permission_resources` is a list of RedLeader resources that
    elastic beanstalk instances should have access to.
    """
    def __init__(self,
                 context,
                 application,
                 options,
                 solution_stack_name,
                 description="",
                 permission_resources=[],
                 instance_profile=None,
                 cf_params={}
    ):
        super().__init__(context, cf_params)
        self._application = application
        self._options = options
        self._solution_stack_name = solution_stack_name
        self._description = description

        self.add_dependency(application)

        self._generated_profile = None
        self._permission_resources = permission_resources
        self._instance_profile = instance_profile
        if instance_profile is not None:
            self.add_dependency(self._instance_profile)

    def generate_sub_resources(self):
        if self._instance_profile is None:
            if self._generated_profile is None:
                self._generated_profile = ElasticBeanstalkInstanceProfile(
                    self._context,
                    self._permission_resources)
                self.add_dependency(self._generated_profile)
            return [self._generated_profile]
        return []

    def generate_options(self):
        service_role_option = {
            "Namespace": "aws:elasticbeanstalk:environment",
            "OptionName": "ServiceRole",
            "Value": Resource.cf_ref(self._generated_profile._ebs_role)
        }
        return [service_role_option]

    @staticmethod
    def format_options(options):
        """
        Format options for cloud formation.
        """
        formatted = []
        for namespace in options:
            for option_name in options[namespace]:
                formatted.append(
                    {
                        "Namespace": namespace,
                        "OptionName": option_name,
                        "Value": options[namespace][option_name]
                    })
        return formatted

    def get_id(self):
        return "elasticBeanstalkConfigTemplate%s%s" % \
            (util.sanitize_name(self._application._name),
             util.sanitize_name(self._description[:10]))

    def _cloud_formation_template(self):
        """
        Get the cloud formation template for this resource
        """
        return {
            "Type": "AWS::ElasticBeanstalk::ConfigurationTemplate",
            "Properties": {
                "ApplicationName": Resource.cf_ref(self._application),
                "Description": self._description,
                "OptionSettings": self.format_options(self._options) + self.generate_options(),
                "SolutionStackName": self._solution_stack_name
            }
        }
