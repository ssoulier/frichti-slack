import json
from urllib.parse import parse_qs

class Action:

    clear = 'clear'
    edit = 'edit'
    order = 'order'
    list_team = 'list_team'
    list_user = 'list_user'
    dishes_added = 'dishes_added'
    undefined = 'undefined'

class CommandIssue:

    not_a_list_argument = 'not_a_list_argument'
    no_issue = 'no_issue'
    oops = 'oops'
    no_dish_type_selected = 'no_dish_type_selected'
    several_commands = 'several_commands'
    not_available_action = 'not_available_action'
    not_available_callback = 'not_available_callback'


class ResponseLayer():

    headers = {'Content-type': 'application/json'}

    responseTemplate = {'statusCode': 200, 'headers': headers}

    def dishes_added_response(self):

        body = {'response_type': 'in_channel', 'text': ''}

        return self.format_response(body)

    def ordered_dishes(self, user_item):

        if 'dishes' in user_item:
            sorted_dishes = sorted(user_item['dishes'], key= lambda x: x['dish_name'])
            for dish_type in CommandHandler.AVAILABLE_DISH_TYPES:
                counter = {}
                result = {'dish_type': dish_type}
                for dish in sorted_dishes:
                    if dish_type == dish['dish_type']:

                        dish_name = dish['dish_name']
                        if dish_name not in counter:
                             counter[dish_name] = 0

                        counter[dish_name] += 1


                result['dishes'] = [{'dish_name': name, 'count': counter[name]} for name in sorted(counter)]
                yield result


    def edit_response(self, user_item):

        attachments = []
        for dishes_per_type in self.ordered_dishes(user_item):
            dish_type = dishes_per_type['dish_type']
            dish_names = dishes_per_type['dishes']
            for dish in dish_names:
                action = {
                    "name": "remove",
                    "text": "Remove",
                    "style": "danger",
                    "type": "button",
                    "value": json.dumps({'dish_type': dish_type, 'dish_name': dish['dish_name']})
                }

                attachment = {
                    "callback_id": "edit",
                    "actions": [action],
                    'text': dish
                }

                attachments.append(attachment)

        if len(attachments):
            body = {'text': 'Which dish would you like to remove from your order ?', 'attachments': attachments}
        else:
            body = {'text': 'There is nothing to edit. Use `/frichti [starter | main | dessert | extra] your favorite dish` to order something for your lunch :yum:'}

        return self.format_response(body)

    def list_user_dishes(self, user_item):
        attachments = []

        for dishes_per_type in self.ordered_dishes(user_item):
            dish_type = dishes_per_type['dish_type']

            attachment = {
                "pretext": dish_type.title(),
                "color": "good"
            }

            fields = []

            for dish in dishes_per_type['dish_names']:
                field = {'short': True}
                dish_name = dish['dish_name']
                count = dish['count']

                if count > 1:
                    field['value'] = "{dish_name}: {count}".format(dish_name=dish_name, count=str(count))
                else:
                    field['value'] = "{dish_name}".format(dish_name=dish_name)

                fields.append(field)

            attachment['fields'] = fields
            attachments.append(attachment)

        if len(attachments):
            body = {'attachments': attachments}
        else:
            body = {'text': 'You did not ordered yet'}

        return self.format_response(body)


    def list_team_dishes(self, team_items):

        if not len(team_items):
            body = {'text': 'Nothing ordered by the team :face_with_rolling_eyes:'}
            return self.format_response(body)

        attachments = []
        for item in sorted(team_items, key= lambda x: x['user_name']):
            user = item['user_name']

            fields = []
            for dishes_per_type in self.ordered_dishes(item):
                dish_type = dishes_per_type['dish_type']
                dish_texts = []
                for dish in dishes_per_type['names']:
                    dish_name = dish['dish_name']
                    count = dish['count']

                    if count > 1:
                        dish_text = '{dish_name} => {count}'.format(dish_name=dish_name, count=count)
                    else:
                        dish_text = '{dish_name}'.format(dish_name=dish_name)

                    dish_texts.append(dish_text)

                fields.append({'title': dish_type.title(), 'value': '\n'.join(dish_texts), 'short': True})

            attachment = {'title': user, 'fields': fields, 'color': 'good'}
            attachments.append(attachment)


        body = {'text': 'The team ordered: ', 'attachments': attachments}
        return self.format_response(body)


    def format_response(self, body):

        response = self.responseTemplate.copy()
        response['body'] = json.dumps(body)

        return response



class CommandHandler():

    AVAILABLE_ACTIONS = ('starter', 'main', 'dessert', 'extra', 'edit', 'clear', 'list', 'order')
    AVAILABLE_DISH_TYPES = ('starter', 'main', 'dessert', 'extra')
    AVAILABLE_CALLBACKS = ('edit')

    def __init__(self,event, db_layer, response_layer):
        self.body = parse_qs(event['body'])
        self.team_id = self.body['team_id'][0]
        self.user_id = self.body['user_id'][0]
        self.user_name = self.body['user_name'][0]
        self.command = self.body['text'][0]
        self.command_issue = CommandIssue.no_issue

        # Only if it's a callback
        self.payload = self.body.get('payload')

        self.db_layer = db_layer
        self.response_layer = response_layer

        self.action = Action.undefined

    def parseCommand(self):
        if '/frichti' in self.command:
            self.command_issue = CommandIssue.several_commands
        else:
            args = self.command.split(' ')
            action = args[0]

            if action not in CommandHandler.AVAILABLE_ACTIONS:
                self.command_issue = CommandIssue.not_available_action

            if action in CommandHandler.AVAILABLE_DISH_TYPES:

                if len(args) == 1:
                    self.command_issue = CommandIssue.no_dish_type_selected

                dishes = ' '.join(args[1:]).split(';')
                dishes = [item.strip() for item in dishes]

                result = self.db_layer.add_dish(self.team_id, self.user_id, self.user_name, action, *dishes)

                if not result:
                    self.command_issue = CommandIssue.oops

                return self.response_layer.dishes_added_response()

            elif action == 'edit':

                result = self.db_layer.get_user_item(self.team_id, self.user_id)

                return self.response_layer.edit_response(result)

            elif action == 'list':

                if len(args) == 1:

                    result = self.db_layer.get_user_item(self.team_id, self.user_id)
                    return self.response_layer.list_user_dishes(result)

                else:
                    if args[1] == 'team':
                        result = self.db_layer.get_team_items(self.team_id)
                        return self.response_layer.list_team_dishes(result)
                    else:
                        self.command_issue = CommandIssue.not_a_list_argument

            elif action == 'order':
                self.action = Action.order

            elif action == 'clear':
                self.db_layer.clear_team(self.team_id)
                self.action = Action.clear
            else:
                self.command_issue = CommandIssue.not_available_action



