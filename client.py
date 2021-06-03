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
TIMEOUT_TIME = 5

USAGE = '''
Usage: {sys.argv[0]} [address]
    address: Server address - can be a port (eg 8000) on localhost, or IP:port (eg 127.0.0.1:8000)
'''

SERVER_ADDRESS = 'localhost', 8000
try:
    if len(sys.argv) > 1:
        if ':' in sys.argv[1]:
            ip, port = sys.argv[1].split(':')
            SERVER_ADDRESS = (ip, int(port))
        else:
            SERVER_ADDRESS = 'localhost', int(sys.argv[1])
except:
    print(USAGE)

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
/leave [room] - Leave current room, or leave [room]
/exit - Exit program
/quit - Exit program
/help - Print this message
/debug - Toggle debug information
'''

# runs on another thread
def listen_on_socket(sockt, responsefn):
    try:
        # make sure app has chance to start main loop
        sleep(0.1)
        sockt.settimeout(5)
        while data := sockt.recv(1024):
            data = json.loads(data.decode())
            if data.op == OpCode.HEART_BEAT:
                continue
            responsefn(data)
    except TimeoutError:
        responsefn({ "op": OpCode.ERR_TIMEOUT })
        return



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

    def __init__(self, name, messages=[]):
        self.name = name
        self.messages = messages

class App(urwid.Pile):

    def __init__(self):
        '''
        Attempts to login and builds UI upon success. Main loop must be started
        separately.
        '''
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
                sockt.sendall(json.dumps(login_data[0]).encode()) # # login username
                resp = sockt.recv(1024).decode()
                resp = json.loads(resp)
                if resp['op'] != OpCode.LOGIN:
                    if resp['op'] == OpCode.ERR_NAME_EXISTS:
                        print('ERROR: Username exists')
                    elif resp['op'] == OpCode.ERR_ILLEGAL_NAME:
                        print('ERROR: Username is illegal')
                    return None

                user = User(resp['username'], sockt)
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

        # self.responses = {
        #     OpCode.MESSAGE: onmessage,

        # }


        welcome_messages = [
            urwid.Text(WELCOME_MSG),
            urwid.Text(f"You are logged in as '{user.username}'")
        ]
        self.rooms = [Room('default', welcome_messages)]
        self.current_room = self.rooms[0]

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
    def printfn(self, string, room=None):
        if not room:
            room = self.current_room
        new_text = urwid.Text(string)
        room.messages.append(new_text)
        if room == self.current_room:
            self.text_widget.body = room.messages
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
        else:
            payload, _ = self.message(input)
        
        return payload
    
    def get_room_by_name(self, room_name):
        for (i, room) in enumerate(self.rooms):
            if room.name == room_name:
                return self.rooms[i]
    
    def switch_current_room(self, room_name):
        for room in self.rooms:
            if room.name == room_name:
                self.current_room = room
                self.text_widget.body = room.messages
                self.loop.draw_screen()
                return
        raise ValueError(f"No room named '{room_name}'\nRooms: {[r.name for r in self.rooms]}")
    
    def handle_server_response(self, response):
        try:
            op = response['op']
        except:
            self.printfn('ERROR: Malformed response from server:')
            self.printfn(response)
            return

        if op == OpCode.MESSAGE:
            message = f'{response["user"]}: {response["MESSAGE"]}'
            if self.current_room.name == response['room']:
                self.printfn(message)
            else:
                if room := self.get_room_by_name(response['room']):
                    room.messages.append(urwid.Text(message))

        elif op == OpCode.LOGIN:
            self.printfn(f'User {response["username"]} has logged in.')

        elif op == OpCode.LIST_USERS:
            self.printfn(f'USERS')
            self.printfn(','.join(response['users']))

        elif op == OpCode.LIST_ROOMS:
            self.printfn(f'ROOMS')
            self.printfn(','.join(response['rooms']))

        elif op == OpCode.JOIN_ROOM:
            if response["user"] == self.user.username:
                room_name = response['room']
                if room_name not in self.rooms:
                    self.rooms.append(Room(room_name, []))
                self.switch_current_room(room_name)
                self.printfn(f'Joined room "{response["room"]}"')
            else:
                self.printfn(f'{response["user"]} has joined {response["room"]}')
        
        elif op == OpCode.USER_EXIT:
            self.printfn(f'''User '{response["user"]}' has logged off''')
        
        elif op == OpCode.ERR_TIMEOUT:
            import os
            self.loop.stop()
            print('Server timed out')
            os._exit(1)
        
        elif op == OpCode.LEAVE_ROOM:
            room_name = response["room"]
            if room_name == 'default':
                self.printfn("Leaving room 'default' is not allowed")
                return
            room = self.get_room_by_name(room_name)
            if room == self.current_room:
                self.switch_current_room('default')
            self.rooms.remove(room)
        
        elif op == OpCode.ERR_ILLEGAL_OP:
            self.printfn('SERVER ERROR: Illegal Operation')

        elif op == OpCode.ERR_NAME_EXISTS:
            self.printfn('SERVER ERROR: Name exists')

        elif op == OpCode.ERR_ILLEGAL_NAME:
            self.printfn('SERVER ERROR: Illegal Name')

        elif op == OpCode.ERR_ILLEGAL_MSG:
            self.printfn('SERVER ERROR: Illegal Message')

        elif op == OpCode.ERR_ILLEGAL_MSG:
            self.printfn('SERVER ERROR: Received malformed request')

        elif op == OpCode.ERR:
            self.printfn(json.loads(response))

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
            self.switch_current_room(room)
            return (None, f'Switched to room {room}')
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
        if msg == '':
            return (None, None)
        payload = { 
            'op': OpCode.MESSAGE,
            'user': UUID,
            'room': self.current_room.name,
            'msg': msg,
            }
        return (payload, None)

    # TODO doesn't work
    def exit_app(self, msg=''):
        import os
        self.loop.stop()
        os._exit(0)

    def help_cmd(self, _=''):
        return (None, HELP_MSG)


def run_client():
    app = App()
    app.loop.run()
    return


if __name__ == '__main__':
    run_client()
    