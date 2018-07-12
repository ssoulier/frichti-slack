# -*- coding: utf-8 -*-

import json
from urllib.parse import parse_qs
import boto3
import os
import requests

AVAILABLE_COMMANDS = ("starter", "main", "dessert", "extra", "edit", "clear", "list", "order")
AVAILABLE_CALLBACK = ("edit")
PLATE_TYPES = ('starter', 'main', 'dessert', 'extra')

dynamo = boto3.resource("dynamodb")
table = dynamo.Table(os.environ['ORDER_TABLE'])

headers = {"Content-type": "application/json"}
responseTemplate = {'statusCode': 200, "headers": headers}


def order(user_id, user_name, plate_type, *plates):
    result = table.update_item(
        Key={
            'user_id': user_id,
            'plate_type': plate_type
        },
        UpdateExpression="SET plates = list_append(if_not_exists(plates, :empty_list), :plates), user_name = :user_name",
        ExpressionAttributeValues={
            ':empty_list': [],
            ':plates': list(plates),
            ':user_name': user_name
        },
        ReturnValues='NONE',
    )

    result = {
        # 'text': 'Coming right up :heavy_check_mark:',
        'text': '',
        'response_type': 'in_channel'
    }

    return (result)


def delete_plate(user_id, plate_type, plate):
    result = table.get_item(
        Key={
            'user_id': user_id,
            'plate_type': plate_type
        },
        ProjectionExpression='plates'
    )

    if 'Item' in result:
        plates = result['Item'].get('plates')

        if plate in plates:
            plates.remove(plate)

            if len(plates):

                result = table.update_item(
                    Key={
                        'user_id': user_id,
                        'plate_type': plate_type
                    },
                    UpdateExpression="SET plates = :plates",
                    ExpressionAttributeValues={
                        ':plates': list(plates),
                    },
                    ReturnValues='NONE',

                )

            else:
                result = table.delete_item(
                    Key={
                        'user_id': user_id,
                        'plate_type': plate_type
                    }
                )

                # todo: deal with all the else cases


def edit(user_id, selected_plate=''):
    items = table.query(
        KeyConditionExpression='user_id = :user_id',
        ExpressionAttributeValues={
            ':user_id': user_id
        },
        ProjectionExpression="plate_type,plates"
    )

    attachments = []
    if 'Items' in items:
        for item in items['Items']:
            for plate_type in PLATE_TYPES:
                if plate_type == item['plate_type']:

                    for plate in item['plates']:
                        action = {
                            "name": "remove",
                            "text": "Remove",
                            "style": "danger",
                            "type": "button",
                            "value": json.dumps({'plate_type': plate_type, 'plate': plate})
                        }

                        attachment = {
                            "callback_id": "edit",
                            "actions": [action],
                            'text': plate
                        }

                        attachments.append(attachment)

    if len(attachments):
        attachment = {
            "callback_id": "edit",
            "actions": [
                {
                    "name": "cancel",
                    "text": "I'm fine",
                    "type": "button",
                    "value": "cancel",
                    "color": "primary"
                }
            ]
        }

        attachments.append(attachment)

        result = {
            "text": "Which plate would you like to remove from your order ?",
            "attachments": attachments
        }

    else:

        result = {
            "text": "There is nothing to edit. Use `/frichti starter your plate name` to order a plate :avocado:"
        }

    return result


def remove(user_id=None, selected_plate=None):
    if user_id:
        if selected_plate:
            delete_plate(user_id, selected_plate['plate_type'], selected_plate['plate'])
            return list_user(user_id, text='Your updated order is')


    else:  # clear the database for a new frichti day
        keys = table.scan(
            ProjectionExpression="user_id,plate_type"
        )

        for key in keys['Items']:
            table.delete_item(
                Key={
                    'user_id': key['user_id'],
                    'plate_type': key['plate_type']
                }
            )

        return {"text": "The db is clean. Team can start order :yum:"}


def list_aggregate():
    items = table.scan(
        ProjectionExpression="user_id,plates,user_name,plate_type",
    )

    attachements = []

    if items["Count"] == 0:
        return {"text": "Nothing ordered by the team :face_with_rolling_eyes:"}
    else:

        plate_types = {}
        for item in items["Items"]:
            plate_type = item['plate_type']
            if plate_type not in plate_types:
                plate_types[plate_type] = {}

            plates = item['plates']
            for plate in plates:
                if plate not in plate_types[plate_type]:
                    plate_types[plate_type][plate] = 0

                plate_types[plate_type][plate] += 1

        for plate_type in ('starter', 'main', 'dessert', 'extra'):

            if plate_type in plate_types:

                attachment = {
                    "pretext": plate_type.title(),
                    "color": "good"
                }

                fields = []
                for plate in sorted(plate_types[plate_type]):
                    count = plate_types[plate_type][plate]
                    field = {'short': True}

                    field['value'] = "{plate}: {count}".format(plate=plate, count=str(count))

                    fields.append(field)

                attachment['fields'] = fields

                attachements.append(attachment)

        return {"attachments": attachements, 'text': 'The team ordered'}


def list_user(user_id, text=None):
    items = table.query(
        KeyConditionExpression='user_id = :user_id',
        ExpressionAttributeValues={
            ':user_id': user_id
        },
        ProjectionExpression="plate_type,plates"
    )

    if items["Count"] == 0:
        return {"text": "You did not order yet."}
    else:
        attachements = []
        plate_types = {}
        for item in items["Items"]:

            plate_type = item['plate_type']
            if plate_type not in plate_types:
                plate_types[plate_type] = {}

            plates = item['plates']
            for plate in plates:
                if plate not in plate_types[plate_type]:
                    plate_types[plate_type][plate] = 0

                plate_types[plate_type][plate] += 1

        for plate_type in ('starter', 'main', 'dessert', 'extra'):

            if plate_type in plate_types:

                attachment = {
                    "pretext": plate_type.title(),
                    "color": "good"
                }

                fields = []
                for plate in sorted(plate_types[plate_type]):
                    count = plate_types[plate_type][plate]
                    field = {'short': True}

                    if count > 1:
                        field['value'] = "{plate}: {count}".format(plate=plate, count=str(count))
                    else:
                        field['value'] = "{plate}".format(plate=plate)

                    fields.append(field)

                attachment['fields'] = fields

                attachements.append(attachment)

        result = {"attachments": attachements}

        if text:
            result['text'] = text
        else:
            result['text'] = 'You ordered'

        return result


def list_team():
    items = table.scan(
        ProjectionExpression="user_id,plates,user_name,plate_type",
    )

    if items["Count"] == 0:
        return {"text": "Nothing ordered by the team :face_with_rolling_eyes:"}
    else:
        users = {}
        for item in items["Items"]:

            user = item['user_name']
            if user not in users:
                users[user] = {}

            plate_type = item['plate_type']
            if plate_type not in users[user]:
                users[user][plate_type] = {}

            plates = item['plates']
            for plate in plates:
                if plate not in users[user][plate_type]:
                    users[user][plate_type][plate] = 0

                users[user][plate_type][plate] += 1

        attachments = []
        for user in sorted(users):

            text_elt = []
            for plate_type in ('starter', 'main', 'dessert', 'extra'):

                if plate_type in users[user]:

                    for plate in sorted(users[user][plate_type]):
                        count = users[user][plate_type][plate]

                        if count > 1:
                            text = '{plate_type}: {plate} => {count}'.format(plate_type=plate_type.title(), plate=plate,
                                                                             count=count)
                        else:
                            text = '{plate_type}: {plate}'.format(plate_type=plate_type.title(), plate=plate)

                        text_elt.append(text)

            if text_elt:

                attachment = {
                    'pretext': '{user_name} ordered:'.format(user_name=user),
                    'text': '\n'.join(text_elt)
                }

                attachments.append(attachment)

        return {"attachments": attachments}


def handler(event, _):
    print(event)
    body = parse_qs(event['body'])

    print(body)

    if 'payload' in body:  # it's an action callback
        payload = json.loads(body["payload"][0])
        callback_id = payload["callback_id"]
        if callback_id in AVAILABLE_CALLBACK:

            action = payload['actions'][0]
            action_name = action['name']
            user_id = payload["user"]["id"]

            if 'plate_list' == action_name:
                selected_plate = action['selected_options'][0]['value']
                callback_result = edit(user_id, selected_plate)
            elif 'remove' == action_name:
                action_value = action['value']
                if action_value:
                    selected_plate = json.loads(action_value)
                    callback_result = remove(user_id, selected_plate)
                else:
                    callback_result = {}
            elif 'cancel' == action_name:
                callback_result = list_user(user_id, text='Your order did not change')
            else:
                # todo: handle case vith not a valid action
                callback_result = {}

            print(callback_result)

            r = requests.post(payload["response_url"], json=callback_result)

            if r.status_code == 200:
                return

    else:
        user_id = body['user_id'][0]
        print(user_id)
        user_name = body['user_name'][0]
        command = body['text'][0]
        if '/frichti' in command:
            result = {"text": "You probably copy/pasted 2 or more `/frichti` commands. Please use it one by one :wink:"}
        else:
            args = command.split(' ')

            action = args[0]
            if (action in AVAILABLE_COMMANDS):

                if action in PLATE_TYPES:
                    if len(args) > 1:
                        plates = ' '.join(args[1:]).split(';')
                        plates = [item.strip() for item in plates]
                    else:
                        plates = []

                    result = order(user_id, user_name, action, *plates)
                elif action == "edit":
                    result = edit(user_id)
                elif action == "clear":
                    result = remove()
                elif action == "list":
                    if len(args) > 1:
                        if args[1] == 'team':
                            result = list_team()
                        else:
                            result = {
                                'text': 'This is a not valid command for `list`. Use `/frichti list` for your order or `/frichti list team` for the team oder.'}
                    else:
                        result = list_user(user_id)
                elif action == "order":
                    result = list_aggregate()
                else:
                    result = {"text": "This feature is not yet implemented :grimacing:"}
            else:

                result = {
                    "text": "This command doesn't exist :grimacing:. Use `starter | main | dessert | extra | edit | list`"}

        response = responseTemplate.copy()
        response['body'] = json.dumps(result)

        return response


if __name__ == '__main__':
    event = {'resource': '/frichti', 'path': '/frichti', 'httpMethod': 'POST', 'headers': {'Accept': 'application/json,*/*', 'Accept-Encoding': 'gzip,deflate', 'CloudFront-Forwarded-Proto': 'https', 'CloudFront-Is-Desktop-Viewer': 'true', 'CloudFront-Is-Mobile-Viewer': 'false', 'CloudFront-Is-SmartTV-Viewer': 'false', 'CloudFront-Is-Tablet-Viewer': 'false', 'CloudFront-Viewer-Country': 'US', 'Content-Type': 'application/x-www-form-urlencoded', 'Host': 'cwpc4sd08l.execute-api.us-east-1.amazonaws.com', 'User-Agent': 'Slackbot 1.0 (+https://api.slack.com/robots)', 'Via': '1.1 5cb08f1fdb064b6046c3b17fe92559f8.cloudfront.net (CloudFront)', 'X-Amz-Cf-Id': 'U2HEc-sfLbYtwwROmEDgQDwAjlRR7Ko1xxUHzCtA5zfsbLcXDAhZNw==', 'X-Amzn-Trace-Id': 'Root=1-5b4757a2-26eeff7d2f29278bf25bb815', 'X-Forwarded-For': '52.207.53.149, 54.182.230.59', 'X-Forwarded-Port': '443', 'X-Forwarded-Proto': 'https', 'X-Slack-Request-Timestamp': '1531402146', 'X-Slack-Signature': 'v0=61d5f963a62c45d3f51c7e646f29406378b7dc74ffc4454411c55d00645cca07'}, 'queryStringParameters': None, 'pathParameters': None, 'stageVariables': None, 'requestContext': {'resourceId': '1n9979', 'resourcePath': '/frichti', 'httpMethod': 'POST', 'extendedRequestId': 'J6qhYGrYIAMF2xw=', 'requestTime': '12/Jul/2018:13:29:06 +0000', 'path': '/dev/frichti', 'accountId': '483879061606', 'protocol': 'HTTP/1.1', 'stage': 'dev', 'requestTimeEpoch': 1531402146491, 'requestId': '8d00c1a1-85d7-11e8-88f4-8d0e0298850e', 'identity': {'cognitoIdentityPoolId': None, 'accountId': None, 'cognitoIdentityId': None, 'caller': None, 'sourceIp': '52.207.53.149', 'accessKey': None, 'cognitoAuthenticationType': None, 'cognitoAuthenticationProvider': None, 'userArn': None, 'userAgent': 'Slackbot 1.0 (+https://api.slack.com/robots)', 'user': None}, 'apiId': 'cwpc4sd08l'}, 'body': 'payload=%7B%22type%22%3A%22interactive_message%22%2C%22actions%22%3A%5B%7B%22name%22%3A%22remove%22%2C%22type%22%3A%22button%22%2C%22value%22%3A%22%7B%5C%22plate_type%5C%22%3A+%5C%22starter%5C%22%2C+%5C%22plate%5C%22%3A+%5C%22poulet%5C%22%7D%22%7D%5D%2C%22callback_id%22%3A%22edit%22%2C%22team%22%3A%7B%22id%22%3A%22TAD1PA6TX%22%2C%22domain%22%3A%22pussycratie%22%7D%2C%22channel%22%3A%7B%22id%22%3A%22DADUGGRV5%22%2C%22name%22%3A%22directmessage%22%7D%2C%22user%22%3A%7B%22id%22%3A%22UADUGGKAB%22%2C%22name%22%3A%22stephane%22%7D%2C%22action_ts%22%3A%221531402146.440287%22%2C%22message_ts%22%3A%221531402143.000363%22%2C%22attachment_id%22%3A%221%22%2C%22token%22%3A%22j96WF0mOCsNFaPBninbGyUnX%22%2C%22is_app_unfurl%22%3Afalse%2C%22response_url%22%3A%22https%3A%5C%2F%5C%2Fhooks.slack.com%5C%2Factions%5C%2FTAD1PA6TX%5C%2F398679068118%5C%2FzxEH19p5eudM0d16rx6z0lDY%22%2C%22trigger_id%22%3A%22397457085090.353057346949.824172e835a38567ebbfacb98d1d5f7f%22%7D', 'isBase64Encoded': False}

    # print(handler(event,None))

    # remove()
    #order('UBHR8116Y', 'cyril.vinot', 'main', "Poulet fermier à l'orange & légumes verts")
    handler(event, None)
    #print(json.dumps(list_user('U8N28JF1V',  text='Your order did not change')))
