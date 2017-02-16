import unittest

from redleader.cluster import Cluster, OfflineContext, AWSContext
from redleader.resources import S3BucketResource

import redleader
from redleader.cluster import Cluster, OfflineContext, AWSContext
from redleader.resources import S3BucketResource, SQSQueueResource, CodeDeployEC2InstanceResource, CodeDeployDeploymentGroupResource, ReadWritePermission

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

    def gen_cluster(self, context):
        cluster = Cluster("testClusterClass", context)
        bucket_name = "testbucketname%s" % 5
        s3Bucket = S3BucketResource(context, bucket_name)
        s3Bucket = S3BucketResource(context, bucket_name+"4")
        s3Bucket = S3BucketResource(context, bucket_name+"5")
        sqsQueue = SQSQueueResource(context, "redleaderTestQueue")
        deploymentGroup = CodeDeployDeploymentGroupResource(context,
                                                            "my_application_name",
                                                            "my_deployment_group")
        ec2Instance = CodeDeployEC2InstanceResource(
            context,
            deploymentGroup,
            permissions=[ReadWritePermission(s3Bucket),
                         ReadWritePermission(sqsQueue)],
            storage=10,
            instance_type="t2.nano",
        )
        cluster.add_resource(sqsQueue)
        cluster.add_resource(s3Bucket)
        cluster.add_resource(ec2Instance)
        cluster.add_resource(deploymentGroup)
        return cluster

    def test_template_idempotence(self):
        context = OfflineContext(aws_profile="testing")

        # Configure our cluster
        cluster = self.gen_cluster(context)
        template = cluster.cloud_formation_template()
        template2 = cluster.cloud_formation_template()
        self.assertEqual(template, template2)

        print("Generating cluster again")
        cluster = self.gen_cluster(context)
        template3 = cluster.cloud_formation_template()
        self.assertEqual(template, template3)
