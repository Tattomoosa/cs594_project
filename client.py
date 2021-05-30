#! /usr/bin/env python

import socket
from time import sleep
from datetime import datetime
import sys
import json
import urwid
from threading import Thread

WELCOME_MSG = "Welcome to IRC!"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
SERVER_ADDRESS = 'localhost', PORT
ROOM_NAME = 'default'

username = 'test user'
data = ''
QUIT_CMDS = ['/quit', '/exit']

def listen_on_socket(sockt, printfn):
    while data := sockt.recv(1024):
        printfn(data.decode())

class Room:

    def __init__(self, messages: []):
        self.messages = messages

class App(urwid.Pile):

    def __init__(self, user):
        # setup urwid UI, self is main app container
        self. rooms = []
        self.chat_messages = [
            urwid.Text(WELCOME_MSG),
            f"You are logged in as '{user.username}'"
            ]
        chat_list_walker = urwid.SimpleFocusListWalker(self.chat_messages)
        self.text_widget = urwid.ListBox(chat_list_walker)
        self.edit_widget = urwid.Edit(' > ')
        self.edit_box = urwid.LineBox(urwid.Filler(self.edit_widget))
        super(App, self).__init__([self.text_widget, (3, self.edit_box)], 1)
        self.loop = urwid.MainLoop(self)

        # setup socket listener
        self.user = user
        self.socket = user.socket
        self.socket_thread = Thread(target=listen_on_socket, args=(self.socket, self.printfn))
        self.socket_thread.start()

    # handles app keypresses (global)
    def keypress(self, size, key):
        if key == 'enter':
            edit_text = self.edit_widget.get_edit_text()
            payload = input_check(edit_text, self.printfn)
            self.printfn(f'SENDING: {payload}')
            self.socket.sendall(json.dumps(payload).encode())
            self.edit_widget.edit_text = ''
        else:
            super(App, self).keypress(size, key)
    
    # prints into chat scroll
    def printfn(self, string):
        new_text = urwid.Text(string)
        self.text_widget.body.append(new_text)
        self.text_widget.set_focus_valign('bottom')
        self.text_widget.set_focus(len(self.text_widget.body) - 1)
        self.loop.draw_screen()

class User:
    def __init__(self, username, sockt):
        self.username = username
        # self.uuid = uuid
        self.socket = sockt


def run_client():
    try:
        sockt = socket.socket(socket.AF_INET)
        sockt.connect(SERVER_ADDRESS)
    except:
        print('Error connecting to server')
        exit(1)

    def attempt_login():
        try:
            print('Enter Username: ', end='')
            username = input()
            login_data = login(username)
            print(login_data[1]) # attempt message
            sockt.sendall(json.dumps(login_data[0]).encode()) # # login username
            resp = sockt.recv(1024)
            resp = resp.decode()
            print(resp)
            resp = json.loads(resp)
            user = User(resp['username'], sockt)
            print(user)
            return user
        except Exception as e:
            raise e

    user = None
    while not user:
        user = attempt_login()

    app = App(user)
    app.loop.run()
    return

UUID = 0
RID = 0

def input_check(input, printfn):

    if input[0:1] == '/':
        # This is kinda dirty but adding blank space to string so it can be split with single
        input+=" "
        command, msg = input.split(' ',1)
        payload = {}
        try:
            payload, msg = COMMANDS[command](msg)
            if msg is not None:
                printfn(msg)
        except:
            printfn("Bad Command")
        jsonobject = json.dumps(payload, indent = 2)
        printfn(jsonobject)
    else:
        payload, _ = message(input)
    
    return payload

def login(name=''):
    payload = { 
        'op':'LOGIN',
        'username':name,
        }
    return (payload, f'Attempting to log in as {name}...')

def list_rooms(_=''):
    payload = {
        'op': 'LIST_ROOMS',
        }
    return (payload, None)

def list_users(_=''):
    payload = { 
        'op':'LIST_USERS',
        }
    return (payload, None)

def join_room(room=''):
    payload = { 
        'op':'JOIN_ROOM',
        'user':UUID,
        'room':RID,
        'new':1,
        }
    return (payload, None)
    
def leave_room(msg=''):
    payload = { 
        'op':'LEAVE_ROOM',
        'room':RID
        }
    return (payload, None)
    
def message(msg=''):
    payload = { 
        'op': 'MESSAGE',
        'user': UUID,
        'room': RID,
        'msg': msg,
        }
    return (payload, None)

# TODO doesn't work
def exit_app(msg=''):
    payload = {
        'op': 'EXIT'
    }

HELP_MSG = '''COMMANDS

Commands are prefixed with '/', which must be the first character of the input text.

/login [username] :
/rooms
'''

def help_cmd(_=''):
    return (None, HELP_MSG)

COMMANDS = {    
    '/login':login, 
    '/rooms':list_rooms, 
    '/users':list_users, 
    '/join':join_room, 
    '/leave':leave_room, 
    '/message':message,
    '/exit':exit_app,
    '/quit':exit_app,
    '/help':help_cmd,
    }


if __name__ == '__main__':
    run_client()
    