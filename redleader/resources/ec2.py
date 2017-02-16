from redleader.resources import Resource
from .iam import IAMInstanceProfileResource
import random
import botocore.exceptions
import redleader.exceptions as exceptions

class EC2InstanceResource(Resource):
    """
    Creates an EC2 server resource.

    permissions (optional):
    If a list of permissions is provided, then an instance profile
    will be created with appropriate permissions.

    security_key_name (optional):
    A security key will automatically be created and stored if none is supplied

    security_group (optional): An EC2SecurityGroupResource
    instance_profile (optional): An IAMInstanceProfileResource
    storage_size (default=20): Size of default block storage
    ami (default=ami-165a0876): An AMI string
    instance_type (default=t2.micro): EC2 instance type
    init_script (optional): Script to be executed on EC2 server start
    """

    DEFAULTS = {
        "permissions": [],
        "security_group": None,
        "security_key_name": None,
        "instance_profile": None,
        "storage_size": 20,
        "ami": "ami-165a0876",
        "instance_type": "t2.micro",
        "region_name": "us-west-1",
        "init_script": "",
        "tags": [],
        "cf_params": {}
    }
    def __init__(self, context, **kwargs):
        for key, value in self.DEFAULTS.items():
            if key in kwargs:
                setattr(self, "_" + key, kwargs[key])
            else:
                setattr(self, "_" + key, value)

        super().__init__(context, self._cf_params)
        self._generated_profile = None

        for permission in self._permissions:
            self.add_dependency(permission.resource)

        if self._security_group is not None:
            self.add_dependency(self._security_group)

        if self._security_key_name is None:
            try:
                ec2 = self._context.get_client('ec2')
            except exceptions.OfflineContextError:
                return
            try:
                response = ec2.create_key_pair(KeyName='redleader_keypair')
                with open("./redleader_keypair.pem", "w") as f:
                    f.write(response['KeyMaterial'])
            except botocore.exceptions.ClientError:
                # Key already exists. We're good to go.
                pass
            self._security_key_name="redleader_keypair"

    def generate_sub_resources(self):
        generated = []

        if self._security_group is None:
            self._security_group = EC2SecurityGroupResource(
                self._context,
                ingressConfigs=[{
                    "IpProtocol" : "tcp",
                    "FromPort" : "22",
                    "ToPort" : "22",
                    "CidrIp" : "0.0.0.0/0"
                }]
            )
            generated.append(self._security_group)
            self.add_dependency(self._security_group)

        if self._instance_profile is not None:
            if self._generated_profile is None:
                self._generated_profile = IAMInstanceProfileResource(
                    self._context, self._permissions, roles=[])
                self.add_dependency(self._generated_profile)
            generated.append(self._generated_profile)

        return generated

    def _cloud_formation_block_device_mappings(self):
        return [{
            "DeviceName" : "/dev/sdm",
            "Ebs" : {
                "VolumeType" : "io1",
                "Iops" : "200",
                "DeleteOnTermination" : "true",
                "VolumeSize" : self._storage_size
            }
        }]

    def _cloud_formation_template(self):
        return {
            "Type" : "AWS::EC2::Instance",
            "Properties" : {
                "ImageId" : self._ami,
                "InstanceType": self._instance_type,
                "IamInstanceProfile": Resource.cf_ref(self._instance_profile),
                "KeyName" : self._security_key_name,
                "SecurityGroupIds": [Resource.cf_ref(self._security_group)],
                "BlockDeviceMappings" : self._cloud_formation_block_device_mappings(),
                "UserData": {"Fn::Base64": self._init_script},
                "Tags": self._tags
            }
        }
        raise NotImplementedError

class EC2SecurityGroupResource(Resource):
    """
    Expects ingress/egress objects in the format:
    {
      "IpProtocol" : "tcp",
      "FromPort" : "80",
      "ToPort" : "80",
      "CidrIp" : "0.0.0.0/0"
    }
    """
    def __init__(self, context, ingressConfigs=[], egressConfigs=[], cf_params={}):
        super().__init__(context, cf_params)
        self._ingressConfigs = ingressConfigs
        self._egressConfigs = egressConfigs

    def _cloud_formation_template(self):
        return {
            "Type" : "AWS::EC2::SecurityGroup",
            "Properties" : {
                #"VpcId" : {"Ref" : "myVPC"},
                "GroupDescription": "RedLeader security group %s" % self._id_placeholder(),
                "SecurityGroupIngress": self._ingressConfigs,
                "SecurityGroupEgress": self._egressConfigs
            }
        }
