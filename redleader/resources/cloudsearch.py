from redleader.resources import Resource
import redleader.exceptions as exceptions

class CloudSearch(Resource):
    """
    Resource modeling a CloudSearch resource.

    Currently only useful for generating access policies.
    """
    def __init__(self,
                 context,
                 domain_name,
                 cf_params={}
    ):
        super(CloudSearch, self).__init__(context, cf_params)
        self._domain_name = domain_name

    def is_static(self):
        return True

    def resource_exists(self):
        return True

    def get_id(self):
        return "cloudSearch"

    def _iam_service_policy(self):
        return {"name": "cloudsearch",
                "params": {
                    "domain_name": self._domain_name
                }
        }

    def _cloud_formation_template(self):
        """
        Get the cloud formation template for this resource
        """
        return None
