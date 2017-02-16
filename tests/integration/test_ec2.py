import unittest
import random
import json
import time

import botocore.exceptions

from redleader.cluster import Cluster, OfflineContext, AWSContext
from redleader.resources import S3BucketResource, EC2InstanceResource, ReadWritePermission, CloudWatchLogs

class TestEC2(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_ec2_instance(self):
        context = AWSContext(aws_profile="testing")

        # Configure our cluster
        cluster = Cluster("testClusterClass", context)
        s3Bucket = S3BucketResource(context, "testbucketname%s" % random.randrange(10000000000000))
        logs = CloudWatchLogs(context)
        ec2Instance = EC2InstanceResource(
            context,
            permissions=[ReadWritePermission(s3Bucket),
                         ReadWritePermission(logs)
            ],
            storage=10,
            instance_type="t2.micro")
        cluster.add_resource(logs)
        cluster.add_resource(s3Bucket)
        cluster.add_resource(ec2Instance)

        template = cluster.cloud_formation_template()
        for sub in template['Resources']:
            print("ID: %s" % sub)
            print(template['Resources'][sub])

        # Delete as a preemptive cleanup step
        cluster.delete()
        time.sleep(5)

        # Test deployment
        x = cluster.deploy()
        while cluster.deployment_status() == "CREATE_IN_PROGRESS":
            time.sleep(5)
            print("Cluster being created...")
        self.assertEqual(cluster.deployment_status(), "CREATE_COMPLETE")

        # Test deletion
        print("Cluster successfully created. Deleting.")
        cluster.delete()
        try:
            while cluster.deployment_status() == "DELETE_IN_PROGRESS":
                time.sleep(5)
                print("Cluster being deleted...")
            self.assertEqual(cluster.deployment_status(), "DELETE_COMPLETE")
            print("Cluster successfully deleted")
        except botocore.exceptions.ClientError:
            print("Stack fully deleted, could not obtain deployment status")
