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
import print_chat as pct
from threading import Thread
import threading
import ctypes
from datetime import datetime


class UserData:
    """
    Storage user data
    """
    def __init__(self):

        self.TOKEN = ''
        self.COMMUNITY_ID = ''
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

        """
        with open('contacts.txt', 'r', encoding="utf8") as file:
            for user in file.readlines():
                user = user.split(':')
                self.CONTACTS.append(str(int(user[0])))
        """

        vk_session = vk_api.VkApi(token=self.TOKEN)
        vk = vk_session.get_api()

        results = vk.groups.getById()
        self.COMMUNITY_ID = results[0]['id']


class DialogData:
    """
    Storage data about this dialog
    """
    def __init__(self, vk_session):

        self.MESSAGES_IDS = []
        self.OPPONENT_ID = ''
        self.OPPONENT_NAME = ''

        self.UNREAD_COUNT = 0

        self.vk = vk_session.get_api()

        self.results = []

    def select_dialog(self):

        ids = []

        def print_list_dialogs():
            print('Your dialogs: ')
            print()

            self.results = vk.messages.getConversations(
                    offset=0,
                    count=200,
                    filter='all',
                )
            for i in range(len(self.results['items'])):
                ids.append(str(self.results['items'][i]['conversation']['peer']['id']))
            info = self.vk.users.get(
                    user_ids=', '.join(ids),
                    fields='online',
                )
            for index, dialog in enumerate(self.results['items']):
                user_id = dialog['conversation']['peer']['id']
                if 'unread_count' in list(dialog['conversation'].keys()):
                    unread = int(dialog['conversation']['unread_count'])
                else:
                    unread = 0
                last_message = dialog['last_message']['text']
                name = info[index]["first_name"] + ' ' + info[index]['last_name']
                online = False
                if int(info[index]["online"]) == 1: online = True

                print('{}) {}'.format(index+1, name), end='')
                if online: print(' [online]', end='')
                if unread > 0: print(' (unread: {})'.format(unread), end='')
                print()

        def select(n):
            n = int(n)

            self.OPPONENT_ID = ids[n-1]
            info = self.vk.users.get(
                    user_ids=self.OPPONENT_ID,
                )
            self.OPPONENT_NAME = info[0]["first_name"] + ' ' + info[0]['last_name']
            if 'unread_count' in list(self.results['items'][n-1]['conversation'].keys()):
                self.UNREAD_COUNT = int(self.results['items'][n-1]['conversation']['unread_count'])
            else:
                self.UNREAD_COUNT = 0

        while True:
            print_list_dialogs()
            print()
            n = str(input('Chose the dialog: '))
            if n == 'exit':
                print('the program is close')
                sys.exit(0)
            elif n == 'upd':
                os.system('cls' if os.name == 'nt' else 'clear')
            else:
                select(n)
                break


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

                elif event.type == VkEventType.MESSAGE_NEW and event.from_me and event.text:
                        chat_draw.new_message(
                                user_data.USER_NAME,
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

                elif event.type == VkEventType.READ_ALL_OUTGOING_MESSAGES:
                    if self.opponent_id == str(event.user_id):
                        if event.from_user:
                            chat_draw.markAsRead()

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

        self.unread = '*'
        self.editable = '(ред.)'

        self.pc = pct.print_chat(time='full')
        self.pc.set_colors([
                (user_data.USER_NAME, user_data.user_color),
                (dialog_data.OPPONENT_NAME, user_data.opponent_color),
            ])
        self.pc.set_header('| Dialog with ' + dialog_data.OPPONENT_NAME + ' |\n+' + '-'*(len(dialog_data.OPPONENT_NAME)+12+2) + '+')


    def new_message(self, sender, text, id):
        self.pc.clear_row()

        ls = self.pc.get_message(1)['sender']

        if ls == '':
            ls = sender

        if not sender == ls:
            self.markAsRead()

        self.pc.add_message(sender, text, mark=[' ' + self.unread])

        dialog_data.MESSAGES_IDS.append(str(id))
        print('> ', end='')


    def edit_message(self, id, text):
        self.pc.clear_row()
        number = len(dialog_data.MESSAGES_IDS) - dialog_data.MESSAGES_IDS.index(str(id))
        self.pc.edit(number, text)
        mark_b = self.pc.has_mark(number)
        if mark_b:
            self.pc.edit_mark(number, ' ' + self.editable)
            self.pc.add_mark(number, self.unread)
        else:
            self.pc.edit_mark(number, ' ' + self.editable)
        print('> ', end='')


    def remove_message(self, id):
        self.pc.clear_row()
        number = len(dialog_data.MESSAGES_IDS) - dialog_data.MESSAGES_IDS.index(str(id))
        self.pc.remove(number)
        del dialog_data.MESSAGES_IDS[dialog_data.MESSAGES_IDS.index(str(id))]
        print('> ', end='')


    def markAsRead(self):
        if not len(dialog_data.MESSAGES_IDS) == 0:
            n = 1
            while n <= len(dialog_data.MESSAGES_IDS):
                if self.pc.has_mark(n):
                    m = self.pc.get_mark(n)
                    if m == [(' ' + self.unread)]:
                        self.pc.remove_mark(n)
                    else:
                        self.pc.edit_mark(n, ' ' + self.editable)
                else:
                    break
                n += 1


    def markAsRead_opponent(self):
        n = 1
        while n <= len(dialog_data.MESSAGES_IDS):
            if self.pc.get_message(n)['sender'] == dialog_data.OPPONENT_NAME:
                if self.pc.has_mark(n):
                    m = self.pc.get_mark(n)
                    if m == [(' ' + self.unread)]:
                        self.pc.remove_mark(n)
                    else:
                        self.pc.edit_mark(n, ' ' + self.editable)
                else:
                    break
                n += 1
            else:
                break


    def loadHistory(self, results):
        h = len(dialog_data.MESSAGES_IDS)
        h = 0
        l = len(results["items"])
        for i in range(h, l):
            info = results["items"][i]
            post = info["text"]

            sender = ''
            if str(info["from_id"]) == str(dialog_data.OPPONENT_ID):
                sender = dialog_data.OPPONENT_NAME
            else:
                sender = user_data.USER_NAME

            time = self.timestamp_to_time(info["date"])
            self.pc.add_message_top(sender, post, time=time, mark=[], prnt=False)
            dialog_data.MESSAGES_IDS.insert(0, str(info["id"]))

        self.pc.reload(self.pc.get_num_messages())

    def loadUnRead(self):
        results = vk.messages.getHistory(
                user_id=str(dialog_data.OPPONENT_ID),
                count=dialog_data.UNREAD_COUNT,
                offset=0,
            )
        self.loadHistory(results)

        for i in range(1, len(results['items'])+1):
            self.pc.add_mark(i, ' ' + self.unread)

    def up_on_occupied_rows(self, len_str):
        self.pc.up_on_occupied_rows(len_str)

    def timestamp_to_time(self, string):
        return datetime.fromtimestamp(int(string)).strftime("%d.%m.%y %H:%M")


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
        chat_draw.loadUnRead()

        print('> ', end='')

        while True:
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
                chat_draw.pc.close()
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

            elif command[0] == 'rd':
                results = vk.messages.markAsRead(
                        peer_id=int(dialog_data.OPPONENT_ID),
                        start_message_id=str(0)
                    )
                chat_draw.markAsRead_opponent()

            elif command[0] == 'history':
                n = int(command[1])
                results = vk.messages.getHistory(
                        user_id=str(dialog_data.OPPONENT_ID),
                        count=n,
                        offset=int(len(dialog_data.MESSAGES_IDS))
                    )
                chat_draw.loadHistory(results)

            else:
                post = " ".join(str(post).split())
                if post != '':
                    results = vk.messages.send(
                            user_ids=str(dialog_data.OPPONENT_ID),
                            message=post,
                            random_id=random.randint(0, sys.maxsize),
                        )
