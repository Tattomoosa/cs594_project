from dataclasses import dataclass

@dataclass
class OpCode:

    ERR = 0x0
    LOGIN = 0x1
    LIST_ROOMS = 0x2
    LIST_USERS = 0x3
    JOIN_ROOM = 0x4 
    LEAVE_ROOM = 0x5
    MESSAGE = 0x6
    USER_EXIT = 0x7
    HEART_BEAT = 0x8
    WHISPER = 0x9

    ERR_UNKNOWN = 0x10
    ERR_ILLEGAL_OP = 0x11
    ERR_ILLEGAL_LEN = 0x12
    ERR_NAME_EXISTS = 0x13
    ERR_ILLEGAL_NAME = 0x14
    ERR_ILLEGAL_MSG = 0x15
    ERR_MALFORMED = 0x16
    ERR_TIMEOUT = 0x17
    ERR_ILLEGAL_WISP = 0x18
