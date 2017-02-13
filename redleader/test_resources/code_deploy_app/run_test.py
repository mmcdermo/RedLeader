import boto3

def main():
    sess = boto3.Session(profile_name="testing", region_name="us-west-1")
    client = sess.client('sqs')
    queues = client.list_queues(QueueNamePrefix="redleaderTestQueue")
    url = queues['QueueUrls'][0]
    client.send_message(
        QueueUrl=url,
        MessageBody='message_from_ec2_server')

    sqsClient = client
    queues = sqsClient.list_queues(QueueNamePrefix="redleaderTestQueue")
    queue_url = queues['QueueUrls'][0]

    messages = sqsClient.receive_message(QueueUrl=queue_url)
    for message in messages['Messages']:
        print(message)
    
if __name__ == '__main__':
    main()
