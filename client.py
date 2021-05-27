#! /usr/bin/env python

import socket
import sys
import json
import urwid
from typing import Dict, Tuple

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
SERVER_ADDRESS = 'localhost', PORT
ROOM_NAME = 'default'


'''
message examples

Keep alive
{
    type: KEEP_ALIVE,
}

Send message
{
    type: CHATMSG,
    roomName: str,
    userName: str

}

Join room
{
    type: JOINROOM,
    roomName: str,
    userName: str,
}

List rooms
{
    type: LISTROOM
}
'''

username = 'test user'
data = ''
QUIT_CMDS = ['/quit', '/exit']

class App(urwid.Pile):

    def __init__(self):
        self.chat_messages = [urwid.Text('item0'), urwid.Text('item1')]
        self.chat_list_walker = urwid.SimpleFocusListWalker(self.chat_messages)
        self.text_widget = urwid.ListBox(self.chat_list_walker)
        self.edit_widget = urwid.Edit(' > ')
        self.edit_box = urwid.LineBox(urwid.Filler(self.edit_widget))
        # self.root_widget = urwid.Pile([text_widget, (3, edit_widget)], 1)
        super(App, self).__init__([self.text_widget, (3, self.edit_box)], 1)


    def keypress(self, size, key):
        if key == 'enter':
            edit_text = self.edit_widget.get_edit_text()
            payload = input_check(edit_text, self.printfn)
            # send payload to server here
            # self.printfn(edit_text)
            self.edit_widget.edit_text = ''
        else:
            super(App, self).keypress(size, key)
    
    def printfn(self, string):
        self.text_widget.body.append(urwid.Text(string))

def run_client():
    app = App()
    loop = urwid.MainLoop(app)
    loop.run()

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
            payload, msg = COMMANDS[command](command, msg)
            if msg is not None:
                printfn(msg)
        except:
            printfn("Bad Command")
        jsonobject = json.dumps(payload, indent = 2)
        printfn(jsonobject)
    else:
        payload = message(input)
    
    return payload

def login(command, name=''):
    payload = { 
        'op':'LOGIN',
        'username':name,
        }
    return (payload, f'Attempting to log in as {name}...')

def list_rooms(command, _=''):
    payload = {
        'op': 'LIST_ROOMS',
        }
    return (payload, None)

def list_users(command, _=''):
    payload = { 
        'op':'LIST_USERS',
        }
    return (payload, None)

def join_room(command, room=''):
    payload = { 
        'op':'JOIN_ROOM',
        'user':UUID,
        'room':RID,
        'new':1,
        }
    return (payload, None)
    
def leave_room(command, msg=''):
    payload = { 
        'op':'LEAVE_ROOM',
        'room':RID
        }
    return (payload, None)
    
def message(command, msg=''):
    payload = { 
        'op':'MESSAGE',
        'user':UUID,
        'room':RID,
        'msg':message,
        }
    return (payload, None)

COMMANDS = {    
    '/login':login, 
    '/rooms':list_rooms, 
    '/users':list_users, 
    '/join':join_room, 
    '/leave':leave_room, 
    '/message':message,
    }


if __name__ == '__main__':
    # input_check(input())
    run_client()
    