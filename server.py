#! /usr/bin/env python3

import socket
import socketserver
import signal
import sys
import os
from datetime import datetime
import uuid
import json
from opcodes import OpCode

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
SERVER_ADDRESS = 'localhost', PORT


client_list = []

class Client():

    def __init__(self, socket):
        self.socket = socket
        self.uuid = uuid.uuid1() # make UUID
        self.username = ' '
        self.rooms = ['default']


# Sends message to all clients
def broadcast_all(message):
    for client in client_list:
        broadcast(client, message)

# Sends message to passed in client
def broadcast(client, message):
    message = json.dumps(message).encode()
    client.socket.sendall(message)

# sends message to room
def broadcast_room(message, room):
    for client in client_list:
        if room in client.rooms:
            broadcast(client, message)

class IrcRequestHandler(socketserver.BaseRequestHandler):

    # handles a new client connection and sets up listen loop for messages/commands
    def handle(self):
        print('handle called, pid: ', os.getpid())
        # add client to client list
        self.client = Client(self.request)
        client_list.append(self.client)
        # listen loop
        while data := self.request.recv(1024):
            data = json.loads(data.strip().decode())
            try:
                COMMANDS[data['op']](data, self.client)
            except:
                message = {
                    'op': OpCode.ERR_ILLEGAL_OP
                }
                broadcast(self.client, message)
            

    # called whenwhen client disconnects
    def finish(self):
        exit_app({},self.client)
        client_list.remove(self.client)
    
def login(payload, client):

    print(f"Logging in User {payload['username']}")
    # if payload['username'] in client_list.username:
    if payload['username'] in [c.username for c in client_list]:
        message = {
            'op': OpCode.ERR_NAME_EXISTS,
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
    rooms = []
    for c in client_list:
        for room in c.rooms:
            rooms += [room]

    rooms = list(set(rooms))

    message = {
        'op': OpCode.LIST_ROOMS,
        'rooms': rooms,
    }
    broadcast(client, message)
    return

def list_users(payload, client):
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
    print(f'{payload["user"]} left room {payload["room"]}')
    client.rooms.remove(payload['room'])
    message = {
        'op': OpCode.LEAVE_ROOM,
        'room': payload['room']
    }
    broadcast(client, message)
    return

def message(payload, client):
    message = {
        'op': OpCode.MESSAGE,
        'user': client.username,
        'room': payload['room'],
        'MESSAGE': payload['msg'],
    }
    broadcast_room(message, payload['room'])
    return

def exit_app(payload, client):
    message = {
        'op': OpCode.USER_EXIT,
        'user': client.username,
    }
    broadcast_all(message)
    return

def help_cmd(payload, client):
    print('User requested help')
    message = {
        'op': OpCode.LOGIN,
        'username':payload['username']
    }
    return

COMMANDS = {    
    'LOGIN':login, 
    'LIST_ROOMS':list_rooms, 
    'LIST_USERS':list_users, 
    'JOIN_ROOM':join_room, 
    'LEAVE_ROOM':leave_room, 
    'MESSAGE':message,
    'EXIT':exit_app,
    'EXIT':exit_app,
    '/help':help_cmd,
    }

if __name__ == '__main__':
    with socketserver.ThreadingTCPServer(SERVER_ADDRESS, IrcRequestHandler) as server:

        # socket would fail when previous run was killed if we didn't reuse address
        server.allow_reuse_address = True
        server.serve_forever()