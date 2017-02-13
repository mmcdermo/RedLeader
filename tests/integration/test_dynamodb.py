import unittest
import time
import json
import random
from collections import OrderedDict

from redleader.cluster import Cluster, OfflineContext, AWSContext
from redleader.resources import DynamoDBTableResource

class TestDynamoDB(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    config = {
        "key_schema": OrderedDict([
            ('primary_key', 'HASH'),
            ('range_key', 'RANGE')
        ]),
        "attribute_definitions": {
            'primary_key': 'S',
            'range_key': 'S',
        }
    }

    def test_dynamodb_table(self):
        context = AWSContext(aws_profile="testing")

        cluster = Cluster("testDynamoDBClusterClass", context)
        name = "redleaderTestTable%s" % str(random.randrange(1000000))
        table = DynamoDBTableResource(context, name,
                                      attribute_definitions=self.config['attribute_definitions'],
                                      key_schema=self.config['key_schema'])
        self.assertEqual(False, table.resource_exists())

        cluster.add_resource(table)
        template = cluster.cloud_formation_template()
        print(json.dumps(template, indent=4))        
        self.assertEqual(1, len(template['Resources'].keys()))

        cluster.blocking_delete(verbose=True)
        cluster.blocking_deploy(verbose=True)

        time.sleep(15)

        # Now ensure that the table doesn't get produced in the cf template
        self.assertEqual(True, table.resource_exists())
        template = cluster.cloud_formation_template()
        print(json.dumps(template, indent=4))
        self.assertEqual(0, len(template['Resources'].keys()))
        cluster.blocking_delete(verbose=True)

