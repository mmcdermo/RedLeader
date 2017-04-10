import unittest
import random
import json
import time
import pkg_resources

import botocore.exceptions

import redleader
from redleader.cluster import Cluster, OfflineContext, AWSContext
from redleader.resources import S3BucketResource, SQSQueueResource, CodeDeployEC2InstanceResource, CodeDeployDeploymentGroupResource, ReadWritePermission
from redleader.managers import CodeDeployManager
from util import cleanup_buckets

class TestCodeDeploy(unittest.TestCase):
    def setUp(self):
        self._context = AWSContext(aws_profile="testing")
        cleanup_buckets(self._context.get_client('s3'), 'testbucketname')

    def tearDown(self):
        cleanup_buckets(self._context.get_client('s3'), 'testbucketname')
        pass

    def test_code_deploy_cluster(self):
        context = self._context

        # Configure our cluster
        cluster = Cluster("testClusterClass", context)
        bucket_name = "testbucketname%s" % 5
        s3Bucket = S3BucketResource(context, bucket_name)
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

        template = cluster.cloud_formation_template()

        for sub in template['Resources']:
            print("ID: %s" % sub)
            print(json.dumps(template['Resources'][sub], indent=4))
        return
        # Delete as a preemptive cleanup step
        cluster.blocking_delete(verbose=True)

        # Deploy cluster
        x = cluster.blocking_deploy(verbose=True)

        print("Deployed. Sleeping for 15.")
        time.sleep(15)

        # Perform a code deploy deployment
        client = context.get_client('codedeploy')
        manager = CodeDeployManager(context)
        resource_package = redleader
        resource_path = '/'.join(('test_resources', 'code_deploy_app'))
        code_deploy_path = pkg_resources.resource_filename("redleader", resource_path)
        deployment_id = manager.create_deployment("my_application_name",
                                                  "my_deployment_group",
                                                  #deploymentGroup.get_id(),
                                                  path=code_deploy_path,
                                                  bucket_name=bucket_name)

        print("Code deploy succeeded with deployment id %s. Sleeping for 30s" % \
              deployment_id)
        time.sleep(30)

        sqsClient = context.get_client("sqs")
        queues = sqsClient.list_queues(QueueNamePrefix="redleaderTestQueue")
        self.assertEqual(len(queues['QueueUrls']), 1)
        queue_url = queues['QueueUrls'][0]

        messages = sqsClient.receive_message(QueueUrl=queue_url)
        if 'Messages' not in messages:
            print(messages)
            self.assertEqual(0, "No messages key in response")
        for message in messages['Messages']:
            print(message)
            print(sqsClient.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                ))
        self.assertEqual(len(messages['Messages']), 1)
        self.assertEqual(messages['Messages'][0]['Body'], 'message_from_ec2_server')

        # Delete cluster
        cluster.blocking_delete(verbose=True)
