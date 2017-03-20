import hashlib
import random
import json
import os
import os.path
import redleader.util as util

class Resource(object):
    def __init__(self, context, cf_params):
        super(Resource, self).__init__()
        self._context = context
        self._dependencies = []
        self._cf_params = cf_params
        self._user_id = None
        self._multiplicity_uid = None
        self._generated_id = None
        self._generated_resources = None

    def get_dependencies(self):
        return self._dependencies

    def is_static(self):
        """
        Static resources only generate cloud formation templates
        when they don't already exist. Example uses: S3 buckets, SQS queues
        """
        return False

    def add_dependency(self, dep):
        """
        Resource dependencies will be included in the cloud formation
        `DependsOn` attribute to ensure correct creation order.

        Dependencies must be added to the cluster or generated
        as subresources of included resources.
        """
        self._dependencies.append(dep)

    def get_id(self):
        """
        Each resource needs a reproducible UID that represents its state and multiplicty
        State: If a key parameter to a resource changes, it's a different resource
        Multiplicity: We need to be able to differentiate identical resources. e.g) t2.micro Instance #3
        Solution:
	  * Utilize _get_multiplicity to track # of identical resources produced
	  * Utilize _idempotent_params() to get a subset of a resource's
	    cloud formation template output, and hash it.
        Implications:
	  * get_id() cannot be used inside of _cloud_formation_template()
	    ** Instead, we'll output the placeholder {resource_id}
        """
        if self._user_id is not None:
            return self._user_id
        if self._generated_id is None:
                class_name = str(self.__class__.__name__).replace("Resource", "")
                param_hash = self._param_hash()
                if self._multiplicity_uid is None:
                    self._multiplicity_uid = Resource._get_multiplicity(class_name + param_hash)
                self._generated_id = "RL%sN%sP%s" % (class_name,
                                                     self._multiplicity_uid,
                                                     param_hash)
                if self._context.pretty_names():
                    h = hashlib.md5()
                    h.update(self._generated_id.encode('utf-8'))

                    ints = []
                    for x in range(2):
                        ints.append(int(h.hexdigest()[x * 8:(x+ 1) * 8], 16))
                    d = self._context.get_dict()

                    pretty_words = ""
                    for i in ints:
                        word = d[i % len(d)].lower().replace("'", "")
                        pretty_words += word[0].upper() + word[1:].lower()

                    self._generated_id = "%s%s%s" % (class_name, self._multiplicity_uid, pretty_words)

        return self._generated_id

    def _id_placeholder(self):
        """
        Placeholder for use in _cloud_formation_template()
        """
        return "{resource_id}"

    def _param_hash(self):
        key_params = self._idempotent_params()
        template = self._cloud_formation_template()
        extracted = {}
        for k in key_params:
            extracted[k] = template['Properties'][k]

        h = hashlib.md5()
        extracted_json = json.dumps(extracted, sort_keys=True)
        h.update(str(extracted_json).encode('utf-8'))
        return str(h.hexdigest()[0:10])

    @classmethod
    def _get_multiplicity(cls, uid):
        if(not hasattr(cls, "_multiplicity_count")):
            cls._multiplicity_count = {}
        if uid in cls._multiplicity_count:
            cls._multiplicity_count[uid] += 1
        else:
            cls._multiplicity_count[uid] = 1
        return cls._multiplicity_count[uid]

    @classmethod
    def reset_multiplicity(cls):
        cls._multiplicity_count = {}

    def _idempotent_params(self):
        """
        Returns the list of cloud formation parameters that must be the same
        in order for two RedLeader resources to refer to the same deployed resource.

        By default we assume that all parameters must be the same.

        Example: we might change an EC2 instance's security group, but want the
        RedLeader resource to refer to the same deployed server.
        """

        template = self._cloud_formation_template()
        return sorted(template['Properties'].keys())

    def iam_service_policies(self):
        """
        Return a list of objects usable by IAMRoleResource to generate
        an IAM role representing access to this resource and its sub resources
        """
        policies = []
        for resource in self.generate_sub_resources():
            policies += resource.iam_service_policies()
        policies.append(self._iam_service_policy())
        return policies

    def _iam_service_policy(self):
        raise NotImplementedError

    def generate_sub_resources(self):
        if self._generated_resources is None:
            self._generated_resources = self._generate_sub_resources()
        return self._generated_resources

    def _generate_sub_resources(self):
        """
        Generate any sub resources, if necessary
        """
        return []

    @staticmethod
    def cf_ref(resource):
        if resource is None:
            return {}
        return {"Ref": resource.get_id()}

    @staticmethod
    def cf_attr(resource, attr):
        return {"Fn::GetAtt": [ resource.get_id(), attr ]}

    @staticmethod
    def replaceValues(obj, replaceMap):
        if isinstance(obj, dict):
            for key in obj:
                if isinstance(obj[key], str):
                    obj[key] = util.multireplace(obj[key], replaceMap)
                else:
                    obj[key] = Resource.replaceValues(obj[key], replaceMap)
        if isinstance(obj, list):
            new = []
            for elem in obj:
                if isinstance(elem, str) and elem in replaceMap:
                    new.append(replaceMap[elem])
                else:
                    new.append(Resource.replaceValues(elem, replaceMap))
            return new
        return obj

    def cloud_formation_template(self):
        """
        Get the cloud formation template for this resource
        """
        if(self.is_static() and self.resource_exists()):
            # Don't create templates for static resources that exist
            return None

        cf_template = self._cloud_formation_template()
        if cf_template is None:
            return None

        for param in self._cf_params:
            cf_template['Properties'][param] = self._cf_params[param]

        replaceMap = {"{resource_id}": self.get_id()}
        for param in cf_template['Properties']:
            cf_template['Properties'] = Resource.replaceValues(cf_template['Properties'], replaceMap)
        cf_template["DependsOn"] = []
        for dependency in self.get_dependencies():
            if(not dependency.is_static() or not dependency.resource_exists()):
                cf_template["DependsOn"].append(dependency.get_id())

        if self.is_static():
            # Don't delete static resources on cluster deletion
            cf_template["DeletionPolicy"] = "Retain"

        return cf_template

    def find_deployed_resources(self):
        """
        Finds already deployed resources that match this resource's configuration
        """
        raise NotImplementedError

class CustomUserResource(Resource):
    """
    CustomUserResource allows a cluster to provision and depend upon
    resources that aren't yet implemented programatically
    """
    def __init__(self, context, template):
        super(self, context)
        self._template = template

    def cloud_formation_template(self):
        """
        Get the cloud formation template for this resource
        """
        return self._template
