from redleader.resources import Resource 

class S3BucketResource(Resource):
    """
    Resource modeling an S3 Bucket
    """
    def __init__(self,
                 context,
                 bucket_name,
                 reuse_if_exists=False,
                 cf_params={}
                 
    ):
        super().__init__(context, cf_params)

        # TODO: Generate random bucket name suffix if reuse_if_exists=False
        self._bucket_name = bucket_name
        self._reuse_if_exists = reuse_if_exists

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
        if(self.find_deployed_resources and self._reuse_if_exists):
            return "empty" # TODO: empty template
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
