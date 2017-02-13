import unittest

from redleader.cluster import Cluster, OfflineContext
from redleader.resources import S3BucketResource
from redleader.awscontext import AWSContext 

class TestInit(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_cluster(self):
        context = OfflineContext(aws_profile="testing")
        cluster = Cluster("test_cluster_class", context)
        template = cluster.cloud_formation_template()
        self.assertTrue(len(template), 0)
