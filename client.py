#! /usr/bin/env python

import socket
from time import sleep
from datetime import datetime
import sys
import json
import urwid
from threading import Thread

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
SERVER_ADDRESS = 'localhost', PORT
ROOM_NAME = 'default'

username = 'test user'
data = ''
QUIT_CMDS = ['/quit', '/exit']

def listen_on_socket(sockt, printfn):
    while True:
        sleep(1)
        printfn(str(datetime.now()))

        # data = sockt.recv(1024)
        # if data:
        #     printfn(data.decode())

class App(urwid.Pile):

    def __init__(self):
        self.chat_messages = [urwid.Text('item0'), urwid.Text('item1')]
        chat_list_walker = urwid.SimpleFocusListWalker(self.chat_messages)
        self.text_widget = urwid.ListBox(chat_list_walker)
        self.edit_widget = urwid.Edit(' > ')
        self.edit_box = urwid.LineBox(urwid.Filler(self.edit_widget))
        super(App, self).__init__([self.text_widget, (3, self.edit_box)], 1)

        self.socket = socket.socket(socket.AF_INET)
        # self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.connect(SERVER_ADDRESS)
        self.socket.settimeout(.1)

        self.loop = urwid.MainLoop(self)
        self.socket_thread = Thread(
            target=listen_on_socket,
            args=(self.socket, self.printfn)
        )
        self.socket_thread.start()

    def keypress(self, size, key):
        if key == 'enter':
            edit_text = self.edit_widget.get_edit_text()
            payload = input_check(edit_text, self.printfn)
            self.socket.sendall(json.dumps(payload).encode())
            # send payload to server here
            # self.printfn(edit_text)
            self.edit_widget.edit_text = ''
        else:
            super(App, self).keypress(size, key)
    
    def printfn(self, string):
        new_text = urwid.Text(string)
        self.text_widget.body.append(new_text)
        self.text_widget.set_focus_valign('bottom')
        self.text_widget.set_focus(len(self.text_widget.body) - 1)
        self.loop.draw_screen()

def run_client():
    app = App()
    app.loop.run()

    return

    username = input('username:')
    # event loop
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(SERVER_ADDRESS)
            data = input(' > ')
            print(f'Sending: {data}')

            # quit if requested
            if data in QUIT_CMDS:
                return

            sock.sendall(f'[{username}] {data}'.encode())

            received = sock.recv(1024)
            # while received := sock.recv(1024):
                # print(f'Received: {received.decode()}')
            print(f'Received: {received.decode()}')
            print(f'Sent: {data}')

            sock.close()

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
    
    printfn(f'PAYLOAD IS {payload}')
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
def exit_app(_=''):
    pass
    #raise urwid.ExitMainLoop("NOT WORKING")
    # exit()

COMMANDS = {    
    '/login':login, 
    '/rooms':list_rooms, 
    '/users':list_users, 
    '/join':join_room, 
    '/leave':leave_room, 
    '/message':message,
    '/exit':exit_app,
    '/quit':exit_app,
    }


if __name__ == '__main__':
    # input_check(input())
    run_client()
    