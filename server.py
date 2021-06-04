#! /usr/bin/env python3

from json.decoder import JSONDecodeError
import socket
import socketserver
import signal
import sys
import os
from time import sleep
from datetime import datetime
from threading import Thread
import uuid
import json
from opcodes import OpCode

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
SERVER_ADDRESS = 'localhost', PORT


client_list = []

class Client():
    '''
    Represents a single connection to a client
    '''

    def __init__(self, socket):
        self.socket = socket
        self.uuid = uuid.uuid1() # make UUID
        self.username = ' '
        self.rooms = ['default']


def broadcast_all(message):
    '''
    calls broadcast on all clients in client_list
    '''
    for client in client_list:
        broadcast(client, message)

def broadcast_room(message, room):
    '''
    Calls broadcast on all clients in a room
    '''
    for client in client_list:
        if room in client.rooms:
            broadcast(client, message)

def broadcast(client, message):
    '''
    Sends an encoded JSON message to specified client
    '''
    message = json.dumps(message).encode()
    client.socket.sendall(message)


def heart_beat():
    '''
    Sends a heart_beat message to all connected clients every second
    '''
    while True:
        sleep(1)
        print("Bump bump")
        message = {
            'op': OpCode.HEART_BEAT,
        }
        broadcast_all(message)

    

class IrcRequestHandler(socketserver.BaseRequestHandler):

    # handles a new client connection and sets up listen loop for messages/commands
    def handle(self):
        print('handle called, pid: ', os.getpid())
        # add client to client list
        self.client = Client(self.request)
        client_list.append(self.client)
        # listen loop
        while data := self.request.recv(1024):
            try:
                data = json.loads(data.strip().decode())
                COMMANDS[data['op']](data, self.client)
            except JSONDecodeError:
                print('ILLEGAL OPERATION:')
                print(data)
                message = {
                    'op': OpCode.ERR_ILLEGAL_OP
                }
                broadcast(self.client, message)
            

    # called whenwhen client disconnects
    def finish(self):
        '''
        cleans up when client disconnects
        '''
        exit_app({},self.client)
        client_list.remove(self.client)
    
def login(payload, client):
    '''
    Handles clients login by checking for acceptable name and sends back a message
    '''

    print(f"Logging in User {payload['username']}")
    # if payload['username'] in client_list.username:
    if payload['username'] in [c.username for c in client_list]:
        message = {
            'op': OpCode.ERR_NAME_EXISTS,
            'user': payload['username']
        }
        broadcast(client, message)
        return
    elif '.' in payload['username']:
        message = {
            'op': OpCode.ERR_ILLEGAL_NAME,
            'user': payload['username']
        }
        broadcast(client, message)
        return

    if len(payload['username']) > 32 or len(payload['username']) < 1:
        message = {
            'op': OpCode.ERR_ILLEGAL_NAME,
            'user': payload['username']
        }
        broadcast(client, message)
        return

    client.username = payload['username']
    message = {
        'op': OpCode.LOGIN,
        'username':payload['username']
    }
    broadcast(client, message)
    return

def list_rooms(payload, client):
    '''
    List all rooms unless containing a . if so it checks if username contained within.
    '''
    rooms = []
    for c in client_list:
        for room in c.rooms:
            rooms += [room]

    rooms = list(set(rooms))

    for room in rooms:
        if '.' in room:
            if client.username not in room:
                rooms.remove(room)

    message = {
        'op': OpCode.LIST_ROOMS,
        'rooms': rooms,
    }
    broadcast(client, message)
    return

def list_users(payload, client):
    '''
    lists all users. can be used in specified room
    '''
    users = []
    print(payload)
    if payload['room'] == '':
        for c in client_list:
            users += [c.username]
    else:
        for c in client_list:
            if payload['room'] in c.rooms:
                users += [c.username]

    message = {
        'op': OpCode.LIST_USERS,
        'users': users,
    }

    broadcast(client, message)
    return

def join_room(payload, client):
    '''
    Adds room to clients list of rooms
    '''
    print(f'{payload["user"]} joined room {payload["room"]}')
    newroom = False
    if payload['room'] not in client.rooms:
        client.rooms += [payload['room']]
        newroom = True

    message = {
        'op': OpCode.JOIN_ROOM,
        'user': payload['user'],
        'room': payload['room'],
        'new': newroom
    }

    broadcast_room(message,payload['room'])
    
    return

def leave_room(payload, client):
    '''
    Removes room from list of rooms.
    '''
    print(f'{payload["user"]} left room {payload["room"]}')
    client.rooms.remove(payload['room'])
    message = {
        'op': OpCode.LEAVE_ROOM,
        'room': payload['room']
    }
    broadcast_room(message, payload['room'])
    return

def message(payload, client):
    '''
    Broadcast message to room.
    '''
    message = {
        'op': OpCode.MESSAGE,
        'user': client.username,
        'room': payload['room'],
        'message': payload['message'],
    }
    broadcast_room(message, payload['room'])
    return

def whisper(payload, client):
    '''
    Makes sure user doesn't whisper self.
    adds room to users list.
    adds room to targets list.
    sends message to room.
    '''
    print(payload)
    if payload['sender'] == payload['target']:
        message = {
            'op': OpCode.ERR_ILLEGAL_WISP,
            'user': payload['sender'],
        }
        broadcast(client,message)
        return

    sender = payload['sender']
    target = payload['target']
    room_name = f"{sender}.{target}"
    room_name_swapped = f"{target}.{sender}"
    print(room_name, room_name_swapped)
    if room_name_swapped in client.rooms:
        room_name = room_name_swapped

    if room_name not in client.rooms:
        client.rooms += [room_name]

    message = {
        'op': OpCode.WHISPER,
        'sender': client.username,
        'target':  payload['target'],
        'room': room_name,
        'message': payload['message'],
    }
    broadcast(client, message)
    matching = [c for c in client_list if c.username == payload['target']]
    if len(matching) > 0:
        reciever = matching[0]
        if room_name not in reciever.rooms:
            reciever.rooms += [room_name]
        broadcast( reciever,message)

    return

def exit_app(payload, client):
    '''
    sends exit opcode
    '''
    message = {
        'op': OpCode.USER_EXIT,
        'user': client.username,
    }
    broadcast_all(message)
    return

def help_cmd(payload, client):
    '''
    return help opcode
    '''
    print('User requested help')
    message = {
        'op': OpCode.LOGIN,
        'username':payload['username']
    }
    return

COMMANDS = {    
    OpCode.LOGIN:login, 
    OpCode.LIST_ROOMS:list_rooms, 
    OpCode.LIST_USERS:list_users, 
    OpCode.JOIN_ROOM:join_room, 
    OpCode.LEAVE_ROOM:leave_room, 
    OpCode.MESSAGE:message,
    OpCode.USER_EXIT:exit_app,
    OpCode.WHISPER:whisper,
    }

if __name__ == '__main__':
    with socketserver.ThreadingTCPServer(SERVER_ADDRESS, IrcRequestHandler) as server:

        # socket would fail when previous run was killed if we didn't reuse address
        server.allow_reuse_address = True
        thread = Thread(target=heart_beat, name='thread-1')
        thread.start()
        server.serve_forever()