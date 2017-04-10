import json
import unittest
import time
import random

from redleader.cluster import Cluster, OfflineContext, AWSContext
from redleader.resources.elasticbeanstalk import *
from redleader.managers import ElasticBeanstalkManager
from util import cleanup_buckets
import requests

class TestElasticbeanstalk(unittest.TestCase):
    def setUp(self):
        self.context = AWSContext(aws_profile="testing", aws_region="us-west-2")
        cleanup_buckets(self.context.get_client('s3'), 'tests3bucket')

    def tearDown(self):
        #cleanup_buckets(self.context.get_client('s3'), 'tests3bucket')
        pass

    def upload_app(self, manager, bucket_name):
        client = self.context.get_client('s3')
        print(bucket_name)
        client.create_bucket(Bucket=bucket_name,
                             CreateBucketConfiguration = {
                                 "LocationConstraint": "us-west-2"
                             })
        root = __file__.split("/")[:-2]
        source_path = "/".join(root + ["test_data", "elasticbeanstalk"])
        bundle_path = "/".join(root + ["tmp", "elasticbeanstalk.zip"])

        manager.create_package(source_path, bundle_path)
        manager.upload_package(bucket_name, bundle_path, "elasticbeanstalk.zip")

    def test_elasticbeanstalk(self):
        cluster = Cluster("testelasticbeanstalk", self.context)

        bucket_name = "tests3bucket" + str(random.randint(0, 100000))
        manager = ElasticBeanstalkManager(self.context)
        self.upload_app(manager, bucket_name)

        app = ElasticBeanstalkAppResource(self.context, "test_app")
        cname_prefix = "ebs-test-" + str(random.randint(0, 1000000))
        version = ElasticBeanstalkAppVersionResource(
            self.context,
            app,
            bucket_name,
            "elasticbeanstalk.zip",
            "v1.0")

        options = {
            "aws:autoscaling:asg": {
                "MinSize": "1",
                "MaxSize": "2"
            },
            "aws:elasticbeanstalk:environment": {
                "EnvironmentType": "LoadBalanced"
            }
        }
        config = ElasticBeanstalkConfigTemplateResource(
            self.context,
            app,
            options,
            solution_stacks["docker"],
            "python elbs config description")

        env = ElasticBeanstalkEnvResource(
            self.context,
            app,
            version,
            config,
            cname_prefix,
            "env description"
        )

        cluster.add_resource(app)
        cluster.add_resource(version)
        cluster.add_resource(config)
        cluster.add_resource(env)
        template = cluster.cloud_formation_template()
        print(json.dumps(template, indent=4))

        cluster.blocking_delete(verbose=True)
        cluster.blocking_deploy(verbose=True)
        time.sleep(10)

        r = requests.get('http://%s.us-west-2.elasticbeanstalk.com/api/test/' % cname_prefix)
        self.assertEqual(r.status_code, 200)
        j = r.json()
        self.assertEqual(j['status'], 'success')
        cluster.blocking_delete(verbose=True)
