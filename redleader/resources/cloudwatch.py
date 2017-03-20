from redleader.resources import Resource
import redleader.exceptions as exceptions

class CloudWatchLogs(Resource):
    """
    Resource modeling a Cloud Watch Logs resource.

    Currently only useful for generating access policies.
    """
    def __init__(self,
                 context,
                 cf_params={}
    ):
        super(CloudWatchLogs, self).__init__(context, cf_params)

    def is_static(self):
        return True

    def resource_exists(self):
        return True

    def get_id(self):
        return "cloudWatchLogs"

    def _iam_service_policy(self):
        return {"name": "cloudwatchlogs",
                "params": {}
        }

    def _cloud_formation_template(self):
        """
        Get the cloud formation template for this resource
        """
        return None
