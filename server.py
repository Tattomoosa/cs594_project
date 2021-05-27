#! /usr/bin/env python3

import socket
import socketserver
import signal
import sys
import os
from datetime import datetime

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

class IrcRequestHandler(socketserver.BaseRequestHandler):

    # handles a new client connection and sets up listen loop for messages/commands
    def handle(self):
        print('handle called, pid: ', os.getpid())
        # add client to client list
        client_list.append(self.request)
        # listen loop
        while data := self.request.recv(1024):
            data = data.strip()
            message = f"{self.client_address[0]}:{self.client_address[1]} -- {data.decode()}"
            print(f'{datetime.now()}::{message}')
            for client in client_list:
                client.sendall(message.encode())
    
    # called whenwhen client disconnects
    def finish(self):
        print('removing client')
        client_list.remove(self.request)


if __name__ == '__main__':
    with socketserver.ThreadingTCPServer(SERVER_ADDRESS, IrcRequestHandler) as server:

        # socket would fail when previous run was killed if we didn't reuse address
        server.allow_reuse_address = True
        server.serve_forever()