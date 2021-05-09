#! /usr/bin/env python3

import socket
import socketserver
import signal
import sys

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
        print('handle called')
        self.data = self.request.recv(1024).strip()
        message = f"{self.client_address[0]} -- {self.data.decode()}"
        print(message)
        self.request.sendall(message.encode())
        server.close_request(self.request)


if __name__ == '__main__':
    with socketserver.TCPServer(SERVER_ADDRESS, IrcRequestHandler) as server:
        
        # set server socket as reusable so no errors if socket is open from a previous run
        server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.serve_forever()
