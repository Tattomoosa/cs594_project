#! /usr/bin/env python

from json.decoder import JSONDecodeError
import os
from server import whisper
import socket
import select
from time import sleep
from datetime import datetime
import sys
import json
import urwid
from threading import Thread

from urwid.main_loop import ExitMainLoop

from opcodes import OpCode

WELCOME_MSG = "Welcome to IRC!"
TIMEOUT_TIME = 1.0
socket.setdefaulttimeout(TIMEOUT_TIME)

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

exit_msg = 'Exited'
# temp
UUID = 0
RID = 0
HELP_MSG = '''
HELP

COMMANDS

Commands are prefixed with '/', which must be the first character of the input text.

/login [username] - Login with [username]
/whisper [username] [message] - send [username] [message] in private room
/rooms - List rooms
/users [room] - List all users, or users in [room]
/join [room] - Join room
/leave [room] - Leave current room, or leave [room]
/exit - Exit program
/quit - Exit program
/help - Print this message
/debug - Toggle debug information
'''

# logs in before showing main interface
def attempt_login(sockt):
    try:
        print('Enter Username: ', end='')
        username = input()
        login_data = login(username)
        # TODO this clears any hearbeats -- we can DO BETTER somehow ??
        _ = sockt.recv(1024)
        sockt.sendall(json.dumps(login_data[0]).encode()) # # login username
        while resp := sockt.recv(1024).decode():
            resp = json.loads(resp)
            opcode = resp['op']
            if opcode != OpCode.LOGIN:

                if opcode == OpCode.HEART_BEAT:
                    continue
                    
                if opcode == OpCode.ERR_NAME_EXISTS:
                    print('ERROR: Username exists')
                elif opcode == OpCode.ERR_ILLEGAL_NAME:
                    print('ERROR: Username is illegal')
                else:
                    print(f'OPCODE: {opcode:#x}')
                    print(f'{resp}')
                    continue

                return None

            user = User(resp['username'], sockt)
            return user
    except TimeoutError as e:
        print('Connection timed out.')
        exit()
    except Exception as e:
        raise e


# runs on another thread
def listen_on_socket(sockt, responsefn):
    # make sure app has chance to start main loop
    sleep(0.1)
    sockt.settimeout(TIMEOUT_TIME)
    try:
        while True:
            read_s, _, _ = select.select([sockt], [sockt], [], TIMEOUT_TIME)

            if len(read_s):
                data = sockt.recv(1024)
                if not len(data):
                    responsefn({ 'op': OpCode.ERR_TIMEOUT })
                    return
                try:
                    data = json.loads(data.decode())
                except JSONDecodeError:
                    raise ValueError('JSON decoding failed. Data is {data}')
                if data['op'] == OpCode.HEART_BEAT:
                    continue
                responsefn(data)
    # signal works just fine in a thread, but yells at us that it can't be in the
    # main thread and throws a ValueError only when the server disconnects.
    # TODO better way??
    except (ValueError, TimeoutError) as e:
        responsefn({ 'op': OpCode.ERR_TIMEOUT })
        raise e




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
        sockt = socket.socket(socket.AF_INET)
        try:
            sockt.connect(SERVER_ADDRESS)
        except ConnectionRefusedError:
            print('Error connecting to server')
            exit()

        user = None
        while not user:
            user = attempt_login(sockt)

        self.debug = False
        self.commands = {    
            '/login': self.cmd_login, 
            '/rooms': self.cmd_list_rooms, 
            '/users': self.cmd_list_users, 
            '/join': self.cmd_join_room, 
            '/leave': self.cmd_leave_room, 
            '/message': self.cmd_message,
            '/whisper': self.cmd_whisper,
            '/exit': self.cmd_exit_app,
            '/quit': self.cmd_exit_app,
            '/help': self.cmd_help_cmd,
            '/debug': self.toggle_debug,
            }

        self.responses = {
            OpCode.MESSAGE: self.rsp_message,
            OpCode.LOGIN: self.rsp_login,
            OpCode.LIST_USERS: self.rsp_list_users,
            OpCode.LIST_ROOMS: self.rsp_list_rooms,
            OpCode.JOIN_ROOM: self.rsp_join_room,
            OpCode.WHISPER: self.rsp_whisper,
            OpCode.USER_EXIT: self.rsp_user_exit,
            OpCode.LEAVE_ROOM: self.rsp_leave_room,
            OpCode.ERR_TIMEOUT: self.rsp_err_timeout,
            OpCode.ERR_ILLEGAL_OP: self.rsp_err_illegal_op,
            OpCode.ERR_NAME_EXISTS  : self.rsp_err_name_exists,
            OpCode.ERR_ILLEGAL_NAME  : self.rsp_err_illegal_name,
            OpCode.ERR_ILLEGAL_MSG  : self.rsp_err_illegal_msg,
            OpCode.ERR_MALFORMED  : self.rsp_err_malformed,
            OpCode.ERR  : self.rsp_err,
        }

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
        # write to this pipe to quit the application
        self.quit_pipe = self.loop.watch_pipe(self.cmd_exit_app)

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
        '''
        Prints to the client display
        '''
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
        '''
        Parses input and potentially executes commands
        '''

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
            payload, _ = self.cmd_message(input)
        
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
        '''
        Responds to a server message, see RESPONSEs
        '''
        try:
            op = response['op']
        except KeyError:
            self.printfn('ERROR: Malformed response from server:')
            self.printfn(response)
            return
        
        respond_fn = None
        try:
            respond_fn = self.responses[op]
        except KeyError:
            raise ValueError(f'UNKOWN OPCODE {op:#x} SERVER RESPONSE {json.dumps(response)}')
        
        if self.debug:
            self.printfn(f'RECEIVING: {json.dumps(response)}')

        if respond_fn:
            respond_fn(response)
        else:
            raise ValueError(f'Respond fn is None -- OPCODE: {op:#x}, Response: {response}')
        
        

    # ==========================================================================
    # RESPONSE operations
    # ==========================================================================

    def rsp_message(self, response):
        '''
        RESPONSE command executed when message received
        '''
        message = f'{response["user"]}: {response["MESSAGE"]}'
        if self.current_room.name == response['room']:
            self.printfn(message)
        else:
            if room := self.get_room_by_name(response['room']):
                self.printfn(message, room)
    
    def rsp_login(self, response):
        '''
        RESPONSE command executed when notified that user logged in
        '''
        self.printfn(f'User {response["username"]} has logged in.')
    
    def rsp_list_users(self, response):
        '''
        RESPONSE command executed when notified that user listed users
        '''
        self.printfn(f'USERS')
        self.printfn(','.join(response['users']))
    
    def rsp_list_rooms(self, response):
        '''
        RESPONSE command executed when notified that user listed rooms
        '''
        self.printfn(f'ROOMS')
        self.printfn(','.join(response['rooms']))
    
    def rsp_join_room(self, response):
        '''
        RESPONSE command executed when notified that user joined room
        '''
        if response["user"] == self.user.username:
            room_name = response['room']
            if room_name not in [r.name for r in self.rooms]:
                self.rooms.append(Room(room_name, []))
            self.switch_current_room(room_name)
            self.printfn(f'Joined room "{response["room"]}"')
        else:
            self.printfn(f'{response["user"]} has joined {response["room"]}')

    def rsp_whisper(self, response):
        '''
        RESPONSE command executed when notified that user sent or received whisper
        '''
        self.printfn("WHISPER SENT")
        room_name = response["room"]
        # notification of message if not in room
        if room_name != self.current_room.name:
            if response['sender'] == self.user.username:
                message = f'You whispered {response["target"]}'
            else:
                message = f'{response["sender"]} whispered you'
            self.printfn(message)
        
        # send message to room
        message = f'{response["sender"]}: {response["MESSAGE"]}'
        if room_name not in [r.name for r in self.rooms]:
            self.rooms.append(Room(room_name, []))
        room = self.get_room_by_name(room_name)
        self.printfn(message, room)
    
    def rsp_user_exit(self, response):
        '''
        RESPONSE command executed when notified that a user exited
        '''
        self.printfn(f'''User '{response["user"]}' has logged off''')
    
    def rsp_leave_room(self, response):
        '''
        RESPONSE command executed when notified that a user exited
        '''
        room_name = response["room"]
        if room_name == 'default':
            self.printfn("Leaving room 'default' is not allowed")
        room = self.get_room_by_name(room_name)
        if room == self.current_room:
            self.switch_current_room('default')
        self.rooms.remove(room)
    
    def rsp_err_timeout(self, response):
        '''
        RESPONSE command executed when notified that server timed out
        '''
        os.write(self.quit_pipe, 'Server timed out'.encode())
    
    def rsp_err_illegal_op(self, response):
        '''
        RESPONSE command executed when notified that user requested illegal operation
        '''
        self.printfn('SERVER ERROR: Illegal Operation')

    def rsp_err_name_exists(self, response):
        '''
        RESPONSE command executed when notified that user requested a username that doesn't exist
        '''
        self.printfn('SERVER ERROR: Name exists')

    def rsp_err_illegal_name(self, response):
        '''
        RESPONSE command executed when notified that user requested a username that is illegal
        '''
        self.printfn('SERVER ERROR: Illegal Name')

    def rsp_err_illegal_msg(self, response):
        '''
        RESPONSE command executed when notified that user tried to send a message that is illegal
        '''
        self.printfn('SERVER ERROR: Illegal Message')

    def rsp_err_malformed(self, response):
        '''
        RESPONSE command executed when a response from the server is malformed
        '''
        self.printfn('SERVER ERROR: Received malformed request')

    def rsp_err_illegal_whisper(self, response):
        '''
        RESPONSE command executed when client requested illegal whisper
        '''
        self.printfn('SERVER ERROR: Illegal whisper')

    def rsp_err(self, response):
        '''
        RESPONSE generic error (currently unused)
        '''
        self.printfn(json.loads(response))



    # ==========================================================================
    # COMMANDS operations
    # ==========================================================================

    def cmd_login(self, name=''):
        '''
        COMMAND request to login as name
        '''
        payload = { 
            'op': OpCode.LOGIN,
            'username':name,
            }
        return (payload, f'Attempting to log in as {name}...')

    def cmd_list_rooms(self, _=''):
        '''
        COMMAND request to list rooms
        '''
        payload = { 'op': OpCode.LIST_ROOMS, }
        return (payload, None)

    def cmd_list_users(self, room=''):
        '''
        COMMAND request to list users
        '''
        payload = { 
            'op': OpCode.LIST_USERS,
            'room': room,
            }
        return (payload, None)

    def cmd_join_room(self, room=''):
        '''
        COMMAND request to join room
        '''
        if room in [r.name for r in self.rooms]:
            self.switch_current_room(room)
            return (None, f'Switched to room {room}')
        payload = { 
            'op': OpCode.JOIN_ROOM,
            'user': self.user.username,
            'room': room,
            }
        return (payload, None)
        
    def cmd_leave_room(self, room=''):
        '''
        COMMAND request to leave room
        '''
        payload = { 
            'op': OpCode.LEAVE_ROOM,
            'room': room
            }
        return (payload, None)
        
    def cmd_message(self, msg=''):
        '''
        COMMAND request to send message
        '''
        if msg == '':
            return (None, None)
        payload = { 
            'op': OpCode.MESSAGE,
            'user': self.user.username,
            'room': self.current_room.name,
            'msg': msg,
            }
        return (payload, None)

    def cmd_whisper(self, msg=''):
        '''
        COMMAND request to send whisper
        '''
        if msg == '':
            return (None, None)
        
        target = None
        try:
            target, msg = msg.split(" ", 1) 
        except:
            self.printfn('ERROR: Expected "/whisper [user] [message]"')
            return (None, None)

        if target == self.user.username:
            self.printfn('ERROR: You cannot whisper yourself')
            return (None, None)

        payload = { 
            'op': OpCode.WHISPER,
            'sender': self.user.username,
            'target': target,
            'msg': msg,
            }
        return (payload, None)

    # TODO doesn't work
    def cmd_exit_app(self, msg=''):
        '''
        Exits app
        '''
        global exit_msg
        if type(msg) == bytes:
            msg = msg.decode()
        exit_msg = msg
        raise urwid.ExitMainLoop()

    def cmd_help_cmd(self, _=''):
        '''
        Prints help command
        '''
        return (None, HELP_MSG)


def run_client():
    app = App()
    app.loop.run()
    print(exit_msg)
    os._exit(0)


if __name__ == '__main__':
    run_client()
    