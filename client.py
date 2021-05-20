#! /usr/bin/env python3

import socket
import sys
import json

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

def run_client():
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

def input_check(input):

    test = input.split()
    # This is kinda dirty but adding blank space to string so it can be split with single
    input+=" "
    command, msg = input.split(' ',1)
    
    print(COMMANDS[command](command, msg))
    payload = {}
    return input

def login(command, name):
    payload = { 
        'op': 'LOGIN',
        'username': name
        }
    return payload

def list_rooms(command, msg):
    payload = { 
        'op': 'LIST_ROOMS',
        }
    return payload

def list_users(command, msg):
    payload = { 
        'op': 'LIST_USERS',
        }
    return payload

def join_room(command, room):
    payload = { 
        'op': 'JOIN_ROOM',
        'user': UUID,
        'room': RID,
        'new': 1,
        }
    return payload
    
def leave_room(command, msg):
    payload = { 
        'op': 'LEAVE_ROOM',
        'room': RID
        }
    return payload
    
def message(command, msg):
    payload = { 
        'op': 'MESSAGE',
        'user': UUID,
        'room': RID,
        'msg': message,
        }
    return payload

COMMANDS = {    
    '/login': login, 
    '/rooms': list_rooms, 
    '/users': list_users, 
    '/join': join_room, 
    '/leave': leave_room, 
    '/message': message,
    }


if __name__ == '__main__':
    #input_check(input())
    run_client()