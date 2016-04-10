import requests
import util
from plugin_handler import PluginInit


class TelegramAPI:
    def __init__(self, bot_token, plugin_list):
        self.url = "https://api.telegram.org/bot{0}/".format(bot_token)
        self.session = requests.session()
        self.update_id = 0
        self.getMe = self.get_me()
        self.plugin_handle = PluginInit(plugin_list, self.getMe)
        self.current_msg = None

    def get_update(self):  # Gets new messages and sends them to plugin_handler
        url = "{}getUpdates?offset={}".format(self.url, self.update_id)
        response = util.fetch(self.session, url)
        for i in response['result']:
            self.current_msg = i['message']
            self.route_return(self.plugin_handle.process_regex(self.current_msg))
            self.update_id = i['update_id'] + 1  # Updates update_id's value

    def route_return(self, returned_value):  # Figures out where plugin return values belong
        content = {}
        if isinstance(returned_value, str):  # If string sendMessage
            content['text'] = returned_value
            self.send_message(content)
        elif isinstance(returned_value, dict):
            if 'text' in returned_value:
                self.send_message(returned_value)
            elif returned_value['method'] == 'forwardMessage':
                del returned_value['forward_message']
                self.forward_message(returned_value)
            elif 'send' in returned_value['method']:  # sendXXXX processed here
                data = {}
                method = returned_value['method'].replace('send', '')
                if 'data' in returned_value:
                    data = returned_value['data']
                if 'file' in returned_value['method']:
                    file = returned_value['file']
                    self.send_file(method, file, data)
                else:
                    self.send_stuff(method, data)

    def get_me(self):  # getMe
        url = "{}getMe".format(self.url)
        return util.fetch(self.session, url)

    def send_message(self, content):  # sendMessage
        url = "{}sendMessage".format(self.url)  # Creates URL
        default = {  # Default return
            'chat_id': self.current_msg['chat']['id'],
            'text': "",
            'parse_mode': "HTML",
            'reply_to_message_id': self.current_msg['message_id']
        }
        try:
            for k, v in content:
                default[k] = v
        except ValueError:
            default['text'] = content['text']
        return util.make_post(self.session, url, default)  # Sends it to off to be sent

    def forward_message(self, content):  # Forwards a message, note2self. add error handling
        url = "{}forwardMessage".format(self.url)  # Creates URL
        default = {  # Default return
            'chat_id': self.current_msg['chat']['id'],
            'from_chat_id': self.current_msg['chat']['id'],
            'message_id': self.current_msg['message_id']
        }
        for k, v in content:
            default[k] = v
        return util.throw(self.session, url, default)

    def send_file(self, method, file, data):  # sendXXXX
        url = "{}send{}".format(self.url, method)
        default = {
            'chat_id': self.current_msg['chat']['id'],
        }
        for k, v in data.items():
            default[k] = v
        util.throw(self.session, url, file, default)

    def send_stuff(self, method, data):  # Combine with send_message, send_file
        url = "{}send{}".format(self.url, method)
        default = {
            'chat_id': self.current_msg['chat']['id'],
        }
        for k, v in data.items():
            default[k] = v
        util.make_post(self.session, url, default)
