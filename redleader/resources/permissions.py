class ResourcePermission(object):
    def __init__(self, resource):
        self.resource=resource

class WritePermission(ResourcePermission):
    def __init__(self, resource):
        super().__init__(resource)

class ReadPermission(ResourcePermission):
    def __init__(self, resource):
        super().__init__(resource)

class ReadWritePermission(ResourcePermission):
    def __init__(self, resource):
        super().__init__(resource)
