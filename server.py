#! /usr/bin/env python3

import socket
import socketserver
import signal
import sys
import os
from datetime import datetime
import uuid
import json

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
        self.rooms = []


def send_all(message):
    print("test log out")
    for client in client_list:
        client.socket.sendall(message.encode())

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
        for client in client_list:
            send_all(f'User:{self.client.username} logged out')
        client_list.remove(self.client)
    
def login(payload, client):
    print(f"Logging in User {payload['username']}")
    client.username = payload['username']
    message = {
        'username':payload['username']
    }
    print(json.dumps(message))
    client.socket.sendall(json.dumps(message).encode())
    return

def list_rooms(payload):
    print('User requested room list')
    return

def list_users(payload):

    print('User requested user list')
    return

def join_room(payload):
    print('User requested to join room')
    return

def leave_room(payload):
    print('User requested leave room')
    return

def message(payload):
    print('User requested to message')
    return

def exit_app(payload):
    print('User left')
    return

def help_cmd(payload):
    print('User requested help')
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