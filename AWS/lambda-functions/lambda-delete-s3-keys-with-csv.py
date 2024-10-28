import json
import urllib.parse
import boto3

print('Loading function')

s3 = boto3.resource('s3')
bucket = s3.Bucket('rss-content-results-images-dev')
objects = bucket.objects.filter(Prefix = 'firstratesearch.com/finance/')



def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))
    # Iterates through all the objects, doing the pagination for you. Each obj
    # is an ObjectSummary, so it doesn't contain the body. You'll need to call
    # get to get the whole body.
    # for obj in bucket.objects.all():
    for obj in objects:
        key = obj.key
        body = obj.get()['Body'].read()
        print(key)

