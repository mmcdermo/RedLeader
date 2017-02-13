import unittest

from redleader.cluster import Cluster, OfflineContext
from redleader.resources import S3BucketResource
from redleader.awscontext import AWSContext 

class TestS3Resource(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_s3(self):
        context = OfflineContext()        
        cluster = Cluster("test_cluster_class", context)

        s3Bucket = S3BucketResource(context, "redleader_test_bucket")

        cluster.add_resource(s3Bucket)
        template = cluster.cloud_formation_template()
        self.asserEqual(1, len(template))
