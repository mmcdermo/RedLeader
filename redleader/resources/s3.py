from redleader.resources import Resource
import redleader.exceptions as exceptions

class S3BucketResource(Resource):
    """
    Resource modeling an S3 Bucket
    """
    def __init__(self,
                 context,
                 bucket_name,
                 cf_params={}
    ):
        super().__init__(context, cf_params)
        self._bucket_name = self._sanitize(bucket_name)

    def _sanitize(self, name):
        return name.lower().replace("-", "").replace("_", "")

    def is_static(self):
        return True

    def get_id(self):
        return "s3Bucket%s" % self._bucket_name

    def _iam_service_policy(self):
        return {"name": "s3",
                "params": {"bucket_name": self._bucket_name}}

    def _cloud_formation_template(self):
        """
        Get the cloud formation template for this resource
        """
        return {
            "Type" : "AWS::S3::Bucket",
            "Properties" : {
                "BucketName" : self._bucket_name,
                "Tags": [{"Key": "redleader-resource-id", "Value": self.get_id()}]
            }
        }

    def resource_exists(self):
        try:
            client = self._context.get_client('s3')
        except exceptions.OfflineContextError:
            return False
        try:
            client.head_bucket(Bucket=self._bucket_name)
            return True
        except Exception as e:
            return False
