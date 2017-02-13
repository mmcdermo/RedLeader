import unittest
import time
import json
import random

from redleader.cluster import Cluster, OfflineContext, AWSContext
from redleader.resources import SQSQueueResource

class TestSQS(unittest.TestCase):
    def setUp(self):
        TestSQS.cleanup_queues()
        pass

    def tearDown(self):
        TestSQS.cleanup_queues()
        pass

    @staticmethod
    def cleanup_queues():
        context = AWSContext(aws_profile="testing")
        client = context.get_client('sqs')
        queues = client.list_queues(QueueNamePrefix="redleaderTestQueue")
        if 'QueueUrls' not in queues:
            return
        for queue_url in queues['QueueUrls']:
            print("Deleting test queue: %s" % queue_url)
            try:
                client.delete_queue(QueueUrl=queue_url)
            except:
                print("Queue deletion hasn't propagated yet")
                pass
    
    def test_sqs_queue(self):
        context = AWSContext(aws_profile="testing")

        cluster = Cluster("testSQSClusterClass", context)
        queue = SQSQueueResource(context, "redleaderTestQueue" +\
                                 str(random.randrange(1000000)))
        self.assertEqual(False, queue.resource_exists())

        cluster.add_resource(queue)
        template = cluster.cloud_formation_template()
        print(json.dumps(template, indent=4))        
        self.assertEqual(1, len(template['Resources'].keys()))

        cluster.blocking_delete(verbose=True)
        cluster.blocking_deploy(verbose=True)

        time.sleep(60)

        # Now ensure that the queue doesn't get produced in the cf template
        self.assertEqual(True, queue.resource_exists())
        template = cluster.cloud_formation_template()
        print(json.dumps(template, indent=4))
        self.assertEqual(0, len(template['Resources'].keys()))
        cluster.blocking_delete(verbose=True)

