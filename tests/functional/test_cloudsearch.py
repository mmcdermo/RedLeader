import unittest

from redleader.cluster import Cluster, OfflineContext
from redleader.resources import CloudSearch
from redleader.cluster import AWSContext

class TestS3Resource(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_s3(self):
        context = OfflineContext()
        cluster = Cluster("test_cluster_class", context)

        cloudsearch = CloudSearch(context, "randomdomain")

        cluster.add_resource(cloudsearch)
        template = cluster.cloud_formation_template()
        print(template)
        self.assertEqual(2, len(template)) # no template yet
