#! /usr/bin/env python3

import socket
import sys

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
            print(f'sending {data}')

            # quit if requested
            if data in QUIT_CMDS:
                return

            sock.sendall(f'[{username}] {data}'.encode())

            received = str(sock.recv(1024), 'utf-8')

            print(f'Sent: {data}')
            print(f'Received: {received}')

            sock.close()

if __name__ == '__main__':
    run_client()