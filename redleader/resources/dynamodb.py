from redleader.resources import Resource
import botocore

class DynamoDBTableResource(Resource):
    """
    Resource modeling a DynamoDB Table.

    If attribute_definitions and key_schema are not provided,
    the resource will not generate a cloud formation template
    and will be useful only for generating IAM policies/roles/profiles.

    key_schema example:
        OrderedDict([
            ('your_primary_key', 'HASH'),
            ('your_range_key', 'RANGE')
         ])
    attribute_definitions example:
         {
            'your_primary_key': 'S',
            'your_range_key': 'N',
            'some_other_column': 'S',
         }
    """
    def __init__(self,
                 context,
                 table_name,
                 attribute_definitions=None,
                 key_schema=None,
                 read_units=1,
                 write_units=1,
                 cf_params={},
                 aws_region=None
    ):
        super(DynamoDBTableResource, self).__init__(context, cf_params)
        self._attribute_definitions = attribute_definitions
        self._key_schema = key_schema
        self._read_units = read_units
        self._write_units = write_units
        self._table_name = table_name
        self._aws_region = aws_region

    def is_static(self):
        return True

    def get_id(self):
        return "DynamoDBTable%s" % self._table_name.replace("-", "").replace("_", "")

    def _iam_service_policy(self):
        params = {
            "safe_table_name": self.get_id(),
            "table_name": self._table_name
        }

        if self._aws_region != None:
            params["aws_region"] = self._aws_region

        return {
            "name": "dynamodb",
            "params": params
        }

    def _cloud_formation_template(self):
        """
        Get the cloud formation template for this resource
        """
        if self._key_schema is None or self._attribute_definitions is None:
            return None

        key_schema = []
        attribute_definitions = []
        for key in self._key_schema:
            key_schema.append({'AttributeName': key,
                              'KeyType': self._key_schema[key]})
        for key in self._attribute_definitions:
            if key in self._key_schema:
                attribute_definitions.append({'AttributeName': key,
                                              'AttributeType': self._attribute_definitions[key]})

        return {
            "Type" : "AWS::DynamoDB::Table",
            "Properties" : {
                "TableName": self._table_name,
                "AttributeDefinitions": attribute_definitions,
                "KeySchema": key_schema,
                "ProvisionedThroughput": {
                    'ReadCapacityUnits': self._read_units,
                    'WriteCapacityUnits': self._write_units
                }
            }
        }

    def resource_exists(self):
        kwargs = {}
        if(self._aws_region != None):
            kwargs["region_name"] = self._aws_region
        client = self._context.get_client("dynamodb", **kwargs)
        try:
            desc = client.describe_table(TableName=self._table_name)
            return True
        except botocore.exceptions.ClientError as e:
            if "not found" in str(e):
                return False
            else:
                raise e
