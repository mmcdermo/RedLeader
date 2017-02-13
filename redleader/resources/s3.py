from redleader.resources import Resource 

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
        self._bucket_name = bucket_name

    def is_static(self):
        return True

    def get_id(self):
        return "s3Bucket%s" % self._bucket_name.replace("-", "")

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
        client = self._context.get_client('s3')
        try:
            client.head_bucket(Bucket=self._bucket_name)
            print("Bucket %s exists" % self._bucket_name)
            return True
        except Exception as e:
            print("Bucket %s doesn't exist: %s" % (self._bucket_name, e))
            return False
