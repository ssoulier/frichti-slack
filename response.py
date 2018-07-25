import json

from parser import CallbackAction, CallbackId, AVAILABLE_DISH_TYPES


class ResponseLayer():
    headers = {'Content-type': 'application/json'}

    responseTemplate = {'statusCode': 200, 'headers': headers}

    def dishes_added_response(self):

        body = {'response_type': 'in_channel', 'text': ''}

        return body

    def ordered_dishes(self, user_item):

        if 'dishes' in user_item:
            sorted_dishes = sorted(user_item['dishes'], key=lambda x: x['dish_name'])
            for dish_type in AVAILABLE_DISH_TYPES:
                counter = {}
                result = {'dish_type': dish_type}
                for dish in sorted_dishes:
                    if dish_type == dish['dish_type']:

                        dish_name = dish['dish_name']
                        if dish_name not in counter:
                            counter[dish_name] = 0

                        counter[dish_name] += 1

                if len(counter):
                    result['dishes'] = [{'dish_name': name, 'count': counter[name]} for name in sorted(counter)]
                    yield result

    def edit_response(self, user_item, selected_option=None):

        options = list()
        for dishes_per_type in self.ordered_dishes(user_item):
            dish_names = dishes_per_type['dishes']
            for dish in dish_names:
                options.append(
                    {
                        'text': dish['dish_name'],
                        'value': dish['dish_name']
                    }
                )

        actions = list()
        # Add the dish_selector
        action_dish_selector = \
            {
                'name': CallbackAction.selected_dish,
                'text': 'Choose the dish',
                'type': 'select',
                'value': '',
                'options': options,
            }

        if selected_option:
            action_dish_selector['selected_options'] = [
                {
                    'text': selected_option,
                    'value': selected_option
                }
            ]

        actions.append(action_dish_selector)

        # Add the remove button and cancel button
        actions.append(
            {
                'name': CallbackAction.remove,
                'text': 'Remove',
                'type': 'button',
                'value': selected_option if selected_option else '',
                'confirm': {
                    'title': 'Are you sure?',
                    'text': 'It\'a good dish!',
                    'ok_text': 'Yes remove it',
                    'dismiss_text': 'You\'re right. Keep it!'
                },
                'style': 'danger'
            }
        )

        actions.append(
            {
                'name': CallbackAction.cancel,
                'text': 'I\'am done removing',
                'type': 'button',
                'value': '',
                'style': 'default'
            }
        )

        attachments = [
            {
                'callback_id': CallbackId.edit,
                'actions': actions,
                'text': 'Choose the dish to remove or cancel'
            }
        ]

        if len(options):
            body = {'text': 'Which dish would you like to remove from your order ?', 'attachments': attachments}
        else:
            body = {
                'text': 'There is nothing to edit. Use `/frichti [starter | main | dessert | extra] your favorite dish` to order something for your lunch :yum:'}

        return body

    def list_user_dishes(self, user_item):
        attachments = []

        for dishes_per_type in self.ordered_dishes(user_item):
            dish_type = dishes_per_type['dish_type']

            attachment = {
                "pretext": dish_type.title(),
                "color": "good"
            }

            fields = []

            for dish in dishes_per_type['dishes']:
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
            body = {'attachments': attachments, 'text': 'Your current order is:'}
        else:
            body = {'text': 'You did not ordered yet'}

        return body

    def order_response(self, team_items):

        if not len(team_items):
            body = {'text': 'Nothing ordered by the team :face_with_rolling_eyes:'}
            return body

        dishes = {}
        for item in team_items:
            for dish in item['dishes']:
                dish_type = dish['dish_type']
                if dish_type not in dishes:
                    dishes[dish_type] = {}

                dish_name = dish['dish_name']
                if dish_name not in dishes[dish_type]:
                    dishes[dish_type][dish_name] = 0

                dishes[dish_type][dish_name] += 1

        attachments = list()
        for dish_type in AVAILABLE_DISH_TYPES:

            if dish_type in dishes:
                attachment = {'title': dish_type.title()}
                fields = list()
                for dish_name, count in sorted(dishes[dish_type].items(), key=lambda x: x[0]):
                    field = {
                        'value': '{dish_name}: {count}'.format(dish_name=dish_name, count=count),
                        'short': True
                    }

                    fields.append(field)

                attachment['fields'] = fields
                attachments.append(attachment)

        body = {
            'text': 'The team ordered',
            'attachments': attachments
        }

        return body

    def list_team_dishes(self, team_items):

        if not len(team_items):
            body = {'text': 'Nothing ordered by the team :face_with_rolling_eyes:'}
            return body

        attachments = []
        for item in sorted(team_items, key=lambda x: x['user_name']):
            user = item['user_name']

            fields = []
            for dishes_per_type in self.ordered_dishes(item):
                dish_type = dishes_per_type['dish_type']
                dish_texts = []
                for dish in dishes_per_type['dishes']:
                    dish_name = dish['dish_name']
                    count = dish['count']

                    if count > 1:
                        dish_text = '{dish_name}: {count}'.format(dish_name=dish_name, count=count)
                    else:
                        dish_text = '{dish_name}'.format(dish_name=dish_name)

                    dish_texts.append(dish_text)

                fields.append({'title': dish_type.title(), 'value': '\n'.join(dish_texts), 'short': True})

            attachment = {'title': user, 'fields': fields, 'color': 'good'}
            attachments.append(attachment)

        body = {'text': 'The team ordered: ', 'attachments': attachments}
        return body

    def clear_db(self):

        actions = list()
        actions.append(
            {
                'name': CallbackAction.cancel,
                'text': 'No I do not!',
                'type': 'button',
                'value': '',
                'style': 'default'
            }
        )

        actions.append(
            {
                'name': CallbackAction.remove,
                'text': 'Yes clear everything!',
                'type': 'button',
                'value': '',
                'style': 'danger'
            }
        )

        body = {
            'text': 'Do you want to clear all the ordered dishes of the team?',
            'attachments': [
                {
                    'callback_id': 'clear',
                    'actions': actions
                }
            ]
        }

        return body

    def cancel_clear_response(self):
        body = {
            'text': 'The db is not cleared. Use `/frichti list team` if you want to inspect it.'
        }

        return body

    def confirm_clear_response(self):
        body = {
            'text': 'The db is empty. Use `/frichti list team` for a confirmation.'
        }

        return body

    def format_response(self, body=None):

        response = self.responseTemplate.copy()
        if body:
            response['body'] = json.dumps(body)

        return response


    def several_commands_response(self):
        return {
            'text': 'You probably copy/pasted 2 or more `/frichti` commands. Please use it one by one :wink:'
        }

    def not_available_action(self):
        return {
            'text' : 'This command doesn\'t exist :grimacing:. Use `starter | main | dessert | extra | edit | list`'
        }

    def not_available_list_action(self):
        return {
            'text': 'This is a not valid command for `list`. Use `/frichti list` for your order or `/frichti list team` for the team oder.'
        }

    def no_dish(self):
        return {
            'text': 'There is no dish in your command.'
        }