from parser import CommandParser
from response import ResponseLayer
from db import dbLayer

db_layer = dbLayer()
response_layer = ResponseLayer()


def endpoint(event, context):

    print(event)
    commandHandler = CommandParser(event, db_layer, response_layer)

    return commandHandler.parse()


if __name__ == '__main__':
    event = {'resource': '/frichti', 'path': '/frichti', 'httpMethod': 'POST', 'headers': {'Accept': 'application/json,*/*', 'Accept-Encoding': 'gzip,deflate', 'CloudFront-Forwarded-Proto': 'https', 'CloudFront-Is-Desktop-Viewer': 'true', 'CloudFront-Is-Mobile-Viewer': 'false', 'CloudFront-Is-SmartTV-Viewer': 'false', 'CloudFront-Is-Tablet-Viewer': 'false', 'CloudFront-Viewer-Country': 'US', 'Content-Type': 'application/x-www-form-urlencoded', 'Host': '7ygr91je19.execute-api.us-east-1.amazonaws.com', 'User-Agent': 'Slackbot 1.0 (+https://api.slack.com/robots)', 'Via': '1.1 91e54ea7c5cc54f4a3500c72b19a2a23.cloudfront.net (CloudFront)', 'X-Amz-Cf-Id': 'ny6ywhSPEHgPb4krV2FCyNGlhu6mDNr6HkMoZlMYnMgOOG0eRrVM2A==', 'X-Amzn-Trace-Id': 'Root=1-5b582a3d-86513a22adf6c017a3f63cfb', 'X-Forwarded-For': '52.207.53.149, 54.182.230.82', 'X-Forwarded-Port': '443', 'X-Forwarded-Proto': 'https', 'X-Slack-Request-Timestamp': '1532504637', 'X-Slack-Signature': 'v0=17cb852620e29474ecc8a8e486861631e58cadb4bdfb02339426e3c54df3a17d'}, 'queryStringParameters': None, 'pathParameters': None, 'stageVariables': None, 'requestContext': {'resourceId': 'cusfmb', 'resourcePath': '/frichti', 'httpMethod': 'POST', 'extendedRequestId': 'KkuJrEdTIAMFpbw=', 'requestTime': '25/Jul/2018:07:43:57 +0000', 'path': '/dev/frichti', 'accountId': '673288181828', 'protocol': 'HTTP/1.1', 'stage': 'dev', 'requestTimeEpoch': 1532504637930, 'requestId': '7d1c04de-8fde-11e8-b040-2ba93113844d', 'identity': {'cognitoIdentityPoolId': None, 'accountId': None, 'cognitoIdentityId': None, 'caller': None, 'sourceIp': '52.207.53.149', 'accessKey': None, 'cognitoAuthenticationType': None, 'cognitoAuthenticationProvider': None, 'userArn': None, 'userAgent': 'Slackbot 1.0 (+https://api.slack.com/robots)', 'user': None}, 'apiId': '7ygr91je19'}, 'body': 'token=j96WF0mOCsNFaPBninbGyUnX&team_id=TAD1PA6TX&team_domain=pussycratie&channel_id=DADUGGRV5&channel_name=directmessage&user_id=UADUGGKAB&user_name=stephane&command=%2Ffrichti&text=starter&response_url=https%3A%2F%2Fhooks.slack.com%2Fcommands%2FTAD1PA6TX%2F404697158261%2Fb9A8IYQU6xiq3mWSFtlHXPs9&trigger_id=405878364966.353057346949.66a90389965e20219a9ab6d318a656ad', 'isBase64Encoded': False}

    print(endpoint(event, None))