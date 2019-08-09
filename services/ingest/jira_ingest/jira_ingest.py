import json
import os
import hashlib
import hmac
import urllib.request
import urllib.parse


def handler(event, context):
    body = event["body"]
    response = post_to_ingest_api(body)
    return {
        'statusCode': response,
        'body': ""
    }

def post_to_ingest_api(body):
    ingest_url = os.getenv("DATAPLATTFORM_JIRA_URL")
    apikey = os.getenv("DATAPLATTFORM_INGEST_APIKEY")
    data = body.encode("ascii")
    try:
        request = urllib.request.Request(ingest_url, data=data, headers={"x-api-key": apikey})
        response = urllib.request.urlopen(request)
        return response.getcode()
    except urllib.request.HTTPError:
        return 500

