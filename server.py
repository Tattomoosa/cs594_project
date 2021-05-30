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
rooms_list = ['default', 'test', 'test2']

#socket, UUID, USERNAME
# dict {UUID: soccket, username}
# dict {room: user1, user2}

class Client():

    def __init__(self, socket):
        self.socket = socket
        self.uuid = uuid.uuid1() # make UUID
        self.username = ' '
        self.rooms = []


# Sends encoded JSON object to all clients
def send_all(message):
    message = json.dumps(message).encode()
    for client in client_list:
        client.socket.sendall(message)
def response(client, message):
    message = json.dumps(message).encode()
    client.socket.sendall(message)

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
            

            #message = f"{self.client_address[0]}:{self.client_address[1]} -- {data.decode()}"
            #print(f'{datetime.now()}::{message}')
            #for client in client_list:
                #client.socket.sendall(message.encode())
            
    
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
    print(rooms_list)
    message = {
        'op': OpCode.LIST_ROOMS,
        'rooms': rooms_list,
    }
    return

def list_users(payload, client):
    print('User requested user list')
    users = []
    for client in client_list:
        users += [client.username]
    message = {
        'op': OpCode.LIST_USERS,
        'users': users,
    }
    return

def join_room(payload, client):
    print('User requested to join room')
    message = {
        'op': OpCode.JOIN_ROOM,
    }
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
        'user': 'username',
        'room': 'default',
        'MESSAGE': payload['message'],
    }
    send_all(message)
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