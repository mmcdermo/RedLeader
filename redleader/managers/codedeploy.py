import os.path
import os
import time
import tarfile
import random
import redleader.util as util

class CodeDeployManager(object):
    def __init__(self, context):
        self._context = context

    def create_code_deploy_package(self, path):
        n = "code_deploy_package%s.tgz" % random.randrange(0, 10000000)
        self.make_tarfile("./%s" % n, path)
        return n

    @staticmethod
    def make_tarfile(output_filename, source_dir):
        with tarfile.open(output_filename, "w:gz") as tar:
            files = os.listdir(source_dir)
            for f in files:
                tar.add(os.path.join(source_dir, f), arcname=f)

    def upload_package(self, bucket_name, path, name):
        print("Uploading %s to bucket %s/%s" % (path, bucket_name, name))
        client = self._context.get_client('s3')
        f = client.upload_file(path, bucket_name, name)
        # TODO. Configure bucket permissions so that an
        #    IAM policy with s3::GetObject is sufficient.
        #    Then we can remove setting ACL to authenticated-read
        client.put_object_acl(Bucket=bucket_name, Key=name,
                              ACL='authenticated-read')
        return f

    def create_deployment(self, application_name, deployment_group_name,
                          path, bucket_name, version="0", blocking=True, verbose=True):
        package = self.create_code_deploy_package(path)
        x = self.upload_package(bucket_name, "./%s" % package, package)
        client = self._context.get_client('codedeploy')
        res = client.create_deployment(
            applicationName=application_name,
            deploymentGroupName=deployment_group_name,
            revision={
                'revisionType': 'S3',
                's3Location': {
                    'bucket': bucket_name,
                    'key': package,
                    'bundleType': 'tgz',
                }
            })
        os.remove(package)
        deploymentId = res['deploymentId']
        if not blocking:
            return deploymentId

        i = 0
        if verbose:
            print("Deploying..")
        while client.get_deployment(deploymentId=deploymentId)['deploymentInfo']['status'] in ["Created", "InProgress"]:
            i += 1
            if verbose:
                util.print_progress(i)
            time.sleep(2)
        if verbose:
            print("Deployment Status: %s" % client.get_deployment(deploymentId=deploymentId)['deploymentInfo']['status'])
        return (deploymentId, client.get_deployment(deploymentId=deploymentId)['deploymentInfo']['status'])
