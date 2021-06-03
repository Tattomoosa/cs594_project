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

    ERR_UNKNOWN = 0xA
    ERR_ILLEGAL_OP = 0xB
    ERR_ILLEGAL_LEN = 0xC
    ERR_NAME_EXISTS = 0xD
    ERR_ILLEGAL_NAME = 0xE
    ERR_ILLEGAL_MSG = 0xF
    ERR_MALFORMED = 0x10
    ERR_TIMEOUT = 0x11
    ERR_ILLEGAL_WISP = 0x12
