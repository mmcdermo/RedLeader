from redleader.resources import Resource

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
                 cf_params={}
    ):
        super(DynamoDBTableResource, self).__init__(context, cf_params)
        self._attribute_definitions = attribute_definitions
        self._key_schema = key_schema
        self._read_units = read_units
        self._write_units = write_units
        self._table_name = table_name

    def is_static(self):
        return True

    def get_id(self):
        return "DynamoDBTable%s" % self._table_name.replace("-", "").replace("_", "")

    def _iam_service_policy(self):
        return {"name": "dynamodb",
                "params": {
                    "safe_table_name": self.get_id(),
                    "table_name": self._table_name
                }}

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
        client = self._context.get_client("dynamodb")
        try:
            desc = client.describe_table(TableName=self._table_name)
            return True
        except Exception as e:
            print("Table %s does not exist: %s" % (self._table_name, e))
            return False
