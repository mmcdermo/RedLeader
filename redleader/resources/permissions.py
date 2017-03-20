class ResourcePermission(object):
    def __init__(self, resource):
        self.resource=resource

class WritePermission(ResourcePermission):
    def __init__(self, resource):
        super(WritePermission, self).__init__(resource)

class ReadPermission(ResourcePermission):
    def __init__(self, resource):
        super(ReadPermission, self).__init__(resource)

class ReadWritePermission(ResourcePermission):
    def __init__(self, resource):
        super(ReadWritePermission, self).__init__(resource)
