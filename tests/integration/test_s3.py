import unittest
import time
import random
import json

from redleader.cluster import Cluster, OfflineContext, AWSContext
from redleader.resources import S3BucketResource

class TestS3(unittest.TestCase):
    def setUp(self):
        TestS3.cleanup_buckets()
        pass

    def tearDown(self):
        TestS3.cleanup_buckets()
        pass

    @staticmethod
    def cleanup_buckets():
        client = AWSContext(aws_profile="testing").get_client("s3")
        for bucket in client.list_buckets()['Buckets']:
            if 'testbucket' in bucket['Name']:
                print("Deleting test bucket: %s" % bucket['Name'])
                listed = client.list_objects_v2(Bucket=bucket['Name'])
                if 'Contents' in listed:
                    objs = listed['Contents']
                    response = client.delete_objects(
                        Bucket=bucket['Name'],
                        Delete={'Objects': [{"Key": x["Key"]} for x in objs]})
                client.delete_bucket(Bucket=bucket['Name'])
    
    def test_s3_bucket(self):
        context = AWSContext(aws_profile="testing")

        cluster = Cluster("testS3ClusterClass", context)
        bucket = S3BucketResource(context, "redleadertestbucket" +\
                                  str(random.randrange(1000000)))
        self.assertEqual(False, bucket.resource_exists())

        cluster.add_resource(bucket)
        template = cluster.cloud_formation_template()
        print("TEMPL")
        print(template['Resources'].keys())
        self.assertEqual(1, len(template['Resources'].keys()))

        cluster.blocking_delete(verbose=True)
        cluster.blocking_deploy(verbose=True)
        time.sleep(10)

        # Now ensure that the bucket doesn't get produced in the cf template
        self.assertEqual(True, bucket.resource_exists())
        template = cluster.cloud_formation_template()
        print(json.dumps(template, indent=4))
        self.assertEqual(0, len(template['Resources'].keys()))        
        cluster.blocking_delete(verbose=True)

