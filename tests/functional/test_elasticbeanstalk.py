import json
import unittest

from redleader.cluster import Cluster, OfflineContext
from redleader.resources.elasticbeanstalk import *

class TestElasticbeanstalk(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_elasticbeanstalk(self):
        context = OfflineContext()
        cluster = Cluster("test_cluster_class", context)

        app = ElasticBeanstalkAppResource(context, "test_app")
        version = ElasticBeanstalkAppVersionResource(
            context,
            app,
            "test_s3_bucket",
            "testdeploy.zip",
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
            context,
            app,
            options,
            solution_stacks["python_3_4"],
            "python elbs config description")

        env = ElasticBeanstalkEnvResource(
            context,
            app,
            version,
            config,
            None,
            "env description"
        )

        cluster.add_resource(app)
        cluster.add_resource(version)
        cluster.add_resource(config)
        cluster.add_resource(env)
        template = cluster.cloud_formation_template()
        print(json.dumps(template, indent=4))
