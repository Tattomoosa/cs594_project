from dataclasses import dataclass

@dataclass
class OpCode:

    ERR = 'ERR'
    LOGIN = 'LOGIN'
    LIST_ROOMS = 'LIST_ROOMS'
    LIST_USERS = 'LIST_USERS'
    JOIN_ROOM = 'JOIN_ROOM'
    LEAVE_ROOM = 'LEAVE_ROOM'
    MESSAGE = 'MESSAGE'
    ERR_UNKNOWN = 0x10
    ERR_ILLEGAL_OP = 0x11
    ERR_ILLEGAL_LEN = 0x12
    ERR_NAME_EXISTS = 0x13
    ERR_ILLEGAL_NAME = 0x14
    ERR_ILLEGAL_MSG = 0x15
    ERR_MALFORMED = 0x16