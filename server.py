#! /usr/bin/env python3

import socket
import socketserver
import signal
import sys
import os

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

class IrcRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        print('handle called, pid: ', os.getpid())
        self.data = self.request.recv(1024).strip()
        message = f"{self.client_address[0]} -- {self.data.decode()}"
        print(f'message is "{message}"')
        # server.close_request(self.request)
        self.request.sendall(message.encode())


if __name__ == '__main__':
    with socketserver.ThreadingTCPServer(SERVER_ADDRESS, IrcRequestHandler) as server:

        # socket would fail when previous run was killed if we didn't reuse address
        server.allow_reuse_address = True
        server.serve_forever()