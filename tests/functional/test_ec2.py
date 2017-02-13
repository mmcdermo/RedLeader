import unittest

from redleader.cluster import Cluster, OfflineContext
from redleader.resources import S3BucketResource, IAMInstanceProfileResource, IAMRoleResource, IAMPolicyResource, EC2InstanceResource

class TestEC2(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_ec2_instance(self):
        context = OfflineContext()
        cluster = Cluster("test_cluster_class", context)

        s3 = S3BucketResource(context, "test_bucket_name")
        ec2 = EC2InstanceResource(context,
                                  storage=10,
                                  instance_type="t2.small")

        cluster.add_resource(s3)
        cluster.add_resource(ec2)
        template = cluster.cloud_formation_template()
        for sub in template:
            print(sub)
