import unittest

from redleader.cluster import Cluster, OfflineContext
from redleader.resources import S3BucketResource, IAMInstanceProfileResource, IAMRoleResource, IAMPolicyResource
from redleader.awscontext import AWSContext 

class TestInit(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_iam(self):
        context = OfflineContext()
        cluster = Cluster("test_cluster_class", context)

        s3 = S3BucketResource(context, "test_bucket_name")
        ipr = IAMInstanceProfileResource(context, [s3])

        cluster.add_resource(ipr)
        cluster.add_resource(s3)
        template = cluster.cloud_formation_template()
        for sub in template:
            print(sub)
