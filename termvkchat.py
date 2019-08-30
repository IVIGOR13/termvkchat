#
# Author: Igor Ivanov
# 2019
#
import time
import random
import sys
import os
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from print_chat import print_chat
from threading import Thread
import threading
import ctypes


class UserData:
    """
    Storage user data
    """
    def __init__(self):

        self.TOKEN = ''
        self.USER_NAME = ''
        self.CONTACTS = []

        self.user_color = 'yellow'
        self.opponent_color = 'green'

        with open('settings.txt', 'r', encoding="utf8") as file:
            for user in file.readlines():
                param = user.split('=')[0]
                if param == 'TOKEN':
                    self.TOKEN = str(user.split('=')[1]).split('\n')[0]
                elif param == 'USER_NAME':
                    self.USER_NAME = str(user.split('=')[1]).split('\n')[0]

        with open('contacts.txt', 'r', encoding="utf8") as file:
            for user in file.readlines():
                user = user.split(':')
                self.CONTACTS.append(str(int(user[0])))


class DialogData:
    """
    Storage data about this dialog
    """
    def __init__(self, vk_session):

        self.MESSAGES_IDS = []
        self.OPPONENT_ID = ''
        self.OPPONENT_NAME = ''

        self.vk = vk_session.get_api()

    def select_dialog(self):
        print('Your contacts: ')
        print()
        info = self.vk.users.get(
                user_ids=', '.join(user_data.CONTACTS),
                fields='online',
            )
        for i, inf in enumerate(info):
            name = inf["first_name"] + ' ' + inf['last_name']

            print('{}){}'.format(i+1, name), end='')

            if int(inf["online"]) == 1:
                print(' [online]', end='')
            print()

        print()

        n = str(input('chose the dialog: '))

        if n == 'exit':
            print('the program is close')
            sys.exit(0)

        n = int(n)

        self.OPPONENT_ID = user_data.CONTACTS[n-1]
        info = self.vk.users.get(
                user_ids=self.OPPONENT_ID,
            )
        self.OPPONENT_NAME = info[0]["first_name"] + ' ' + info[0]['last_name']



class ChatListener(Thread):
    """
    Listen LongPoll
    """
    def __init__(self, vk_session):

        Thread.__init__(self)

        self.longpoll = VkLongPoll(vk_session)

        self.opponent_name = dialog_data.OPPONENT_NAME
        self.opponent_id = dialog_data.OPPONENT_ID

    def run(self):
        try:
            for event in self.longpoll.listen():

                if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                    if self.opponent_id == str(event.user_id):
                        if event.from_user:
                            chat_draw.new_message(
                                    self.opponent_name,
                                    event.text,
                                    event.message_id
                                )

                elif event.type == VkEventType.MESSAGE_EDIT:
                    if self.opponent_id == str(event.user_id):
                        if event.from_user:
                            chat_draw.edit_message(
                                    event.message_id,
                                    event.text
                                )

                elif event.type == VkEventType.MESSAGE_FLAGS_SET:
                    if self.opponent_id == str(event.user_id):
                        if event.from_user:
                            chat_draw.remove_message(
                                    event.message_id
                                )

        finally:

            print('Dialog with {} is close'.format(self.opponent_name))

    def get_id(self):
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def raise_exception(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
              ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print('Exception raise failure')


class ChatDraw:
    """
    Draw chat
    """
    def __init__(self):

        self.pc = print_chat(time=True)
        self.pc.set_colors([
                (user_data.USER_NAME, user_data.user_color),
                (dialog_data.OPPONENT_NAME, user_data.opponent_color),
            ])
        self.pc.add_skip('| Dialog with ' + dialog_data.OPPONENT_NAME + ' |\n+' + '-'*(len(dialog_data.OPPONENT_NAME)+12+2) + '+')

    def new_message(self, sender, text, id):
        self.pc.clear_row()
        self.pc.add_message(sender, text)
        dialog_data.MESSAGES_IDS.append(str(id))
        print('> ', end='')

    def edit_message(self, id, text):
        self.pc.clear_row()
        number = len(dialog_data.MESSAGES_IDS) - dialog_data.MESSAGES_IDS.index(str(id))
        self.pc.edit(number, text)
        print('> ', end='')

    def remove_message(self, id):
        self.pc.clear_row()
        number = len(dialog_data.MESSAGES_IDS) - dialog_data.MESSAGES_IDS.index(str(id))
        self.pc.remove(number)
        del dialog_data.MESSAGES_IDS[dialog_data.MESSAGES_IDS.index(str(id))]
        print('> ', end='')

    def up_on_occupied_rows(self, len_str):
        self.pc.up_on_occupied_rows(len_str)




if __name__ == "__main__":

    user_data = UserData()

    vk_session = vk_api.VkApi(token=user_data.TOKEN)
    vk = vk_session.get_api()

    dialog_data = DialogData(vk_session)

    while True:

        os.system('cls' if os.name == 'nt' else 'clear')

        dialog_data.select_dialog()

        chat_listener = ChatListener(vk_session)
        chat_listener.start()

        chat_draw = ChatDraw()

        print('> ', end='')

        while  True:

            post = input()

            chat_draw.up_on_occupied_rows(len(user_data.USER_NAME) + len(post) + 2)

            command = post.split(' ')

            vk = vk_session.get_api()

            if post == 'exit':
                chat_listener.raise_exception()
                time.sleep(0.5)
                results = vk.messages.delete(
                        message_ids=1,
                        delete_for_all=0,
                    )
                chat_listener.join()

                time.sleep(1)
                os.system('cls' if os.name == 'nt' else 'clear')
                break

            elif command[0] == 'del':
                results = vk.messages.delete(
                        message_ids=str(dialog_data.MESSAGES_IDS[len(dialog_data.MESSAGES_IDS) - int(command[1])]),
                        delete_for_all=0,
                    )

            elif command[0] == 'delfa':
                results = vk.messages.delete(
                        message_ids=str(dialog_data.MESSAGES_IDS[len(dialog_data.MESSAGES_IDS) - int(command[1])]),
                        delete_for_all=1,
                    )

            elif command[0] == 'edit':
                results = vk.messages.edit(
                        peer_id=int(dialog_data.OPPONENT_ID),
                        message_id=str(dialog_data.MESSAGES_IDS[len(dialog_data.MESSAGES_IDS) - int(command[1])]),
                        message=str(command[2]),
                    )

            else:
                results = vk.messages.send(
                        user_ids=str(dialog_data.OPPONENT_ID),
                        message=post,
                        random_id=random.randint(0, sys.maxsize),
                    )
                chat_draw.new_message(
                        user_data.USER_NAME,
                        post,
                        results[0]['message_id']
                    )
