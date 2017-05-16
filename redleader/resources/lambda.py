from redleader.resources import Resource
import botocore

class LambdaFunctionResource(Resource):
    """
    Resource modeling a Lambda FunctionArn
    """
    def __init__(self,
                 context,
                 function_name,
    ):
        super(DynamoDBTableResource, self).__init__(context, cf_params)
        self._function_name = function_name

    def is_static(self):
        return True

    def get_id(self):
        return "Lambda%s" % self._table_name.replace("-", "").replace("_", "")

    def _iam_service_policy(self):
        return {"name": "lambda",
                "params": {
                    "safe_function_name": self.get_id(),
                    "function_name": self._function_name
                }}

    def _cloud_formation_template(self):
        """
        Get the cloud formation template for this resource
        """
        return {
            "Type" : "AWS::Lambda::Function",
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
        except botocore.exceptions.ClientError as e:
            if "exist" in str(e):
                return False
            else:
                raise e
