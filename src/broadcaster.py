import json

import requests
from settings import params

telegram_chat_id = params.get_config('chats', 'telegram_channel')
telegram_debug_chat_id = params.get_config('chats', 'telegram_channel_debug')
slack_channel = params.get_config('chats', 'slack_channel')
telegram_token = params.get_config('tokens', 'telegram_token')
slack_token = params.get_config('tokens', 'slack_token')
telegram_url = params.get_config('urls', 'telegram_broadcast_url')

headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
}


def send_telegram(message, view_type):
    '''
    Отправляем результаты тестов в телеграм канал
    :param message:     сообщение
    :param view_type:   тип тестов default/debug
    '''

    if view_type in 'default':
        chat_id = telegram_chat_id
    else:
        # Дебаг тестов шлем в другой канал
        chat_id = telegram_debug_chat_id

    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }

    requests.post('{telegram_url}{token}/sendMessage'.format(telegram_url=telegram_url, token=telegram_token),
                  data=data, headers=headers, verify=False)
    return 'ok'


def send_slack(data, view_type):
    '''
    Отправляем результаты тестов в слак канал
    :param message:     сообщение
    :param view_type:   тип тестов default/debug
    '''
    formdata = data

    if view_type not in 'default':
        # игнорируем дебаг
        return 'ok'

    data = {
        'token': slack_token,
        'channel': slack_channel,
        'attachments': json.dumps(formdata),
        'as_user': 'true'
    }
    requests.post('https://slack.com/api/chat.postMessage', data=data, headers=headers, verify=False)
    return 'ok'
