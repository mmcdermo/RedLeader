def cleanup_buckets(client, search_string):
    for bucket in client.list_buckets()['Buckets']:
        if search_string in bucket['Name']:
            print("Deleting test bucket: %s" % bucket['Name'])
            listed = client.list_objects_v2(Bucket=bucket['Name'])
            if 'Contents' in listed:
                objs = listed['Contents']
                response = client.delete_objects(
                    Bucket=bucket['Name'],
                    Delete={'Objects': [{"Key": x["Key"]} for x in objs]})
            client.delete_bucket(Bucket=bucket['Name'])
