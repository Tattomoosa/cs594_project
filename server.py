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

'''
response examples

Keep alive?

Joined room
{
    type: JOINROOM,
    status: SUCCESS,
}

'''


client_list = []

#socket, UUID, USERNAME
# dict {UUID: soccket, username}
# dict {room: user1, user2}

class Client():

    def __init__(self, socket):
        self.socket = socket
        self.uuid = uuid.uuid1() # make UUID
        self.username = ' '
        self.rooms = ['default']


# Sends encoded JSON object to all clients
def send_all(message):
    for client in client_list:
        response(client, message)

def response(client, message):
    message = json.dumps(message).encode()
    client.socket.sendall(message)

def broadcast_room(message, room):
    for client in client_list:
        if room in client.rooms:
            response(client, message)

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

            COMMANDS[data['op']](data, self.client)
            

    # called whenwhen client disconnects
    def finish(self):
        send_all(f'User:{self.client.username} logged out')
        client_list.remove(self.client)
    
def login(payload, client):
    print(f"Logging in User {payload['username']}")
    client.username = payload['username']
    message = {
        'op': OpCode.LOGIN,
        'username':payload['username']
    }
    response(client, message)
    return

def list_rooms(payload, client):
    print('User requested room list')
    rooms = []
    for c in client_list:
        for room in c.rooms:
            rooms += [room]

    rooms = list(set(rooms))

    message = {
        'op': OpCode.LIST_ROOMS,
        'rooms': rooms,
    }
    response(client, message)
    return

def list_users(payload, client):
    print('User requested user list')
    users = []
    print(payload)
    if payload['room'] == '':
        for c in client_list:
            users += [c.username]
    else:
        for c in client_list:
            if payload['room'] in c.rooms:
                users += [client.username]

    message = {
        'op': OpCode.LIST_USERS,
        'users': users,
    }

    response(client, message)
    return

def join_room(payload, client):
    print('User requested to join room')
    newroom = False
    if payload['room'] not in client.rooms:
        client.rooms += [payload['room']]
        newroom = True

    message = {
        'op': OpCode.JOIN_ROOM,
        'user': payload['user'],
        'new': newroom
    }

    broadcast_room(message,payload['room'])
    
    return

def leave_room(payload, client):
    print('User requested leave room')
    message = {
        'op': OpCode.LEAVE_ROOM,
    }
    return

def message(payload, client):
    message = {
        'op': OpCode.MESSAGE,
        'user': client.username,
        'room': payload['room'],
        'MESSAGE': payload['msg'],
    }
    for c in client_list:
        if payload['room'] in c.rooms:
            response(c, message) 
    return

def exit_app(payload, client):
    print('User left')
    # Remove user from rooms
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