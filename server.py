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
            print(data['op'])
            if data['op'] == 'LOGIN':
                self.client.username = data['username']
            
            print(self.client.username)
            print(self.client.uuid)

            #message = f"{self.client_address[0]}:{self.client_address[1]} -- {data.decode()}"
            #print(f'{datetime.now()}::{message}')
            #for client in client_list:
                #client.socket.sendall(message.encode())
            
    
    # called whenwhen client disconnects
    def finish(self):
        print('removing client')
        client_list.remove(self.client)
    

def login(payload):

    return
def list_rooms(payload):
    return
def list_users(payload):
    return
def join_room(payload):
    return
def leave_room(payload):
    return
def message(payload):
    return
def exit_app(payload):
    return
def help_cmd(payload):
    return


COMMANDS = {    
    'LOGIN':login, 
    'LIST_ROOMS':list_rooms, 
    'LIST_USERS':list_users, 
    'JOIN_ROOM':join_room, 
    'LEAVE_ROOM':leave_room, 
    'MESSAGE':message,
    'EXIT':exit_app,
    '/help':help_cmd,
    }

if __name__ == '__main__':
    with socketserver.ThreadingTCPServer(SERVER_ADDRESS, IrcRequestHandler) as server:

        # socket would fail when previous run was killed if we didn't reuse address
        server.allow_reuse_address = True
        server.serve_forever()