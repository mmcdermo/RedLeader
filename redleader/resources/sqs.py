from redleader.resources import Resource
import redleader.exceptions as exceptions

class SQSQueueResource(Resource):
    """
    Resource modeling an S3 Bucket
    """
    def __init__(self,
                 context,
                 queue_name,
                 cf_params={}
    ):
        super(SQSQueueResource, self).__init__(context, cf_params)
        self._queue_name = queue_name

    def is_static(self):
        return True

    def get_id(self):
        return "s3Queue%s" % self._queue_name.replace("-", "").replace("_", "")

    def _iam_service_policy(self):
        return {"name": "sqs",
                "params": {"queue_name": self._queue_name}}


    def _cloud_formation_template(self):
        """
        Get the cloud formation template for this resource
        """
        return {
            "Type" : "AWS::SQS::Queue",
            "Properties" : {
                #"DelaySeconds": Integer,
                #"MaximumMessageSize": Integer,
                #"MessageRetentionPeriod": Integer,
                 "QueueName": self._queue_name
                #"ReceiveMessageWaitTimeSeconds": Integer,
                # "RedrivePolicy": RedrivePolicy,
                # "VisibilityTimeout": Integer
              }
        }

    def resource_exists(self):
        try:
            client = self._context.get_client('s3')
        except exceptions.OfflineContextError:
            return False

        client = self._context.get_client('sqs')
        queues = client.list_queues(QueueNamePrefix=self._queue_name)
        if 'QueueUrls' in queues and len(queues['QueueUrls']) > 0:
            return True
        return False
