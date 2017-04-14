import os.path
import os
import time
import tarfile
import random
from zipfile import ZipFile
import redleader.util as util
import botocore

class ElasticBeanstalkManager(object):
    def __init__(self, context):
        self._context = context

    def upload_package(self, bucket_name, path, name):
        print("Uploading %s to bucket %s/%s" % (path, bucket_name, name))
        client = self._context.get_client('s3')
        try:
            client.create_bucket(Bucket=bucket_name,
                                 CreateBucketConfiguration = {
                                     "LocationConstraint": self._context._aws_region
                                 })
        except botocore.exceptions.ClientError:
            print("Bucket %s already exists" % bucket_name)

        f = client.upload_file(path, bucket_name, name)
        # TODO. Configure bucket permissions so that an
        #    IAM policy with s3::GetObject is sufficient.
        #    Then we can remove setting ACL to authenticated-read
        client.put_object_acl(Bucket=bucket_name, Key=name,
                              ACL='authenticated-read')
        return f

    @staticmethod
    def recursively_add_files_to_zip(source_path, zipfile, base=""):
        for filename in os.listdir(source_path):
            if os.path.isdir(os.path.join(source_path, filename)):
                recursively_add_files_to_zip(os.path.join(source_path, filename), zipfile, os.path.join(base, filename))
            else:
                os.chmod(os.path.join(source_path, filename), 776)
                zipfile.write(os.path.join(source_path, filename), os.path.join(base, filename))

    def create_package(self, source_path, zipfilepath):
        if os.path.isfile(zipfilepath):
            os.remove(zipfilepath)

        with ZipFile(zipfilepath, 'w') as zipfile:
            self.recursively_add_files_to_zip(source_path, zipfile)

        os.chmod(zipfilepath, 776)
        print("Created elastic beanstalk package at %s" % zipfilepath)
        return zipfilepath
