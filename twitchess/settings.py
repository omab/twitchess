import os

# fille with app key/secret and associated account key/secret
APP_KEY        = None
APP_SECRET     = None
ACCOUNT_KEY    = None
ACCOUNT_SECRET = None

# t2chess configuration directory
T2CHESS_DIR_NAME = '.t2chess'
T2CHESS_DIR_PATH = os.path.join(os.environ['HOME'], T2CHESS_DIR_NAME)

# file where to store last read message id
LASTMSGID_FILENAME = 'last_msgid'
SOCKET_FILENAME    = 'queue.sock'
LASTMSGID_FILE     = os.path.join(T2CHESS_DIR_PATH, LASTMSGID_FILENAME)
PLAYQUEUE_SOCKET   = os.path.join(T2CHESS_DIR_PATH, SOCKET_FILENAME)
CHECK_INTERVAL     = 30 # check each 30s


try:
    from local_settings import *
except ImportError:
    pass
