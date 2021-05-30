#! /usr/bin/env python

import socket
from time import sleep
from datetime import datetime
import sys
import json
import urwid
from threading import Thread

from opcodes import OpCode

WELCOME_MSG = "Welcome to IRC!"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
SERVER_ADDRESS = 'localhost', PORT
# temp
UUID = 0
RID = 0
HELP_MSG = '''
HELP

COMMANDS

Commands are prefixed with '/', which must be the first character of the input text.

/login [username] - Login with [username]
/rooms - List rooms
/users [room] - List all users, or users in [room]
/join [room] - Join room
/leave room - Leave room

TODO - more
'''

# runs on another thread
def listen_on_socket(sockt, responsefn):
    # make sure app has chance to start main loop
    sleep(0.1)
    while data := sockt.recv(1024):
        responsefn(json.loads(data.decode()))

def login(name=''):
    payload = { 
        'op': OpCode.LOGIN,
        'username':name,
        }
    return (payload, f'Attempting to log in as {name}...')
        

class User:
    def __init__(self, username, sockt):
        self.username = username
        self.socket = sockt

class Room:

    def __init__(self, name: str, messages: []):
        self.name = name
        self.messages = messages

class App(urwid.Pile):

    def __init__(self):
        # attempt to connect to server socket
        try:
            sockt = socket.socket(socket.AF_INET)
            sockt.connect(SERVER_ADDRESS)
        except ConnectionRefusedError:
            print('Error connecting to server')
            exit()

        # logs in before showing main interface
        def attempt_login():
            try:
                print('Enter Username: ', end='')
                username = input()
                login_data = login(username)
                print(login_data[1]) # attempt message
                sockt.sendall(json.dumps(login_data[0]).encode()) # # login username
                resp = sockt.recv(1024).decode()
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

        self.debug = False
        self.commands = {    
            '/login': self.login, 
            '/rooms': self.list_rooms, 
            '/users': self.list_users, 
            '/join': self.join_room, 
            '/leave': self.leave_room, 
            '/message': self.message,
            '/exit': self.exit_app,
            '/quit': self.exit_app,
            '/help': self.help_cmd,
            '/debug': self.toggle_debug,
            }

        self.current_room_index = 0

        welcome_messages = [
            urwid.Text(WELCOME_MSG),
            urwid.Text(f"You are logged in as '{user.username}'")
            ]
        self.rooms = [Room('default', welcome_messages)]

        # setup urwid UI, self is main app container
        chat_list_walker = urwid.SimpleFocusListWalker(self.current_room.messages)
        self.text_widget = urwid.ListBox(chat_list_walker)
        self.edit_widget = urwid.Edit(' > ')
        self.edit_box = urwid.LineBox(urwid.Filler(self.edit_widget))
        super(App, self).__init__([self.text_widget, (3, self.edit_box)], 1)
        self.loop = urwid.MainLoop(self)

        # setup socket listener
        self.user = user
        self.socket = user.socket
        self.socket_thread = Thread(target=listen_on_socket, args=(self.socket, self.handle_server_response))
        self.socket_thread.start()
    
    def toggle_debug(self, _=''):
        self.debug = not self.debug
        return (None, f"DEBUG IS [{'ON' if self.debug else 'OFF'}]")

    # handles app keypresses (global)
    def keypress(self, size, key):
        if key == 'enter':
            edit_text = self.edit_widget.get_edit_text()
            payload = self.input_check(edit_text)
            if payload:
                if self.debug:
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

    def input_check(self, input):

        if input[0:1] == '/':
            if ' ' in input:
                command, msg = input.split(' ',1)
            else:
                command, msg = input, ''
            payload = None
            try:
                payload, msg = self.commands[command](msg)
                if msg is not None:
                    self.printfn(msg)
            except KeyError:
                self.printfn(f"Bad Command '{command}'")
            # if payload:
            #     jsonobject = json.dumps(payload, indent = 2)
            #     self.printfn(jsonobject)
        else:
            payload, _ = self.message(input)
        
        return payload
    
    @property
    def current_room(self):
        return self.rooms[self.current_room_index]
    
    def set_current_room(self, room_index):
        self.current_room_index = room_index
        room = self.current_room
        self.text_widget.body = room.messages
    
    def switch_current_room_by_name(self, room_name):
        for (i, name) in enumerate(self.rooms):
            if name == room_name:
                self.set_current_room(i)
                return
        raise ValueError(f"No room named '{room_name}'")
    
    def handle_server_response(self, response):
        op = response['op']
        if op == OpCode.MESSAGE:
            self.printfn(f'{response["user"]}: {response["MESSAGE"]}')
        elif op == OpCode.LOGIN:
            self.printfn(f'User {response["user"]} has logged in.')
        elif op == OpCode.LIST_USERS:
            self.printfn(f'USERS')
            self.printfn(','.join(response['users']))
        elif op == OpCode.LIST_ROOMS:
            self.printfn(f'ROOMS')
            self.printfn(','.join(response['rooms']))
        else:
            self.printfn(f'UKNOWN OPCODE {op}')
            self.printfn(json.dumps(response))

    # COMMANDS operations

    def login(self, name=''):
        payload = { 
            'op': OpCode.LOGIN,
            'username':name,
            }
        return (payload, f'Attempting to log in as {name}...')

    def list_rooms(self, _=''):
        payload = {
            'op': OpCode.LIST_ROOMS,
            }
        return (payload, None)

    def list_users(self, room=''):
        payload = { 
            'op': OpCode.LIST_USERS,
            'room': room,
            }
        return (payload, None)

    def join_room(self, room=''):
        if room in [r.name for r in self.rooms]:
            self.switch_current_room_by_name(room)
            return
        payload = { 
            'op': OpCode.JOIN_ROOM,
            'user': self.user.username,
            'room': room,
            # 'new':1,
            }
        return (payload, None)
        
    def leave_room(self, room=''):
        payload = { 
            'op': OpCode.LEAVE_ROOM,
            'room': room
            }
        return (payload, None)
        
    def message(self, msg=''):
        payload = { 
            'op': OpCode.MESSAGE,
            'user': UUID,
            'room': self.current_room.name,
            'msg': msg,
            }
        return (payload, None)

    # TODO doesn't work
    def exit_app(self, msg=''):
        exit()

    def help_cmd(self, _=''):
        return (None, HELP_MSG)


def run_client():
    app = App()
    app.loop.run()
    return


if __name__ == '__main__':
    run_client()
    