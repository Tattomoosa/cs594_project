# README.md

This is an IRC server and client demonstrating the protocol we developed for the
final project in the Internetworking Protocols course at Portland State University
in Spring 2021.

This is intended as a protocol demonstration and is not recommended for production use.

## Protocol

The protocol is described in detail in the [RFC document](./CS594_494_IRC_RFC.pdf).

## Client Commands

```txt
/login [username] - Login with [username]
/whisper [username] [message] - send [username] [message] in private room
/rooms - List rooms
/currentroom - Prints the name of the current room
/users [room] - List all users, or users in [room]
/join [room] - Join room
/leave [room] - Leave current room, or leave [room]
/exit - Exit program
/quit - Exit program
/help - Print this message
/debug - Toggle debug information
```
