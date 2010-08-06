from __future__ import with_statement

import os
import sys
import time
from ConfigParser import ConfigParser, NoOptionError

import tweepy


T2CHESS_DIR_NAME = '.t2chess'
T2CHESS_DIR_PATH = os.path.join(os.environ['HOME'], T2CHESS_DIR_NAME)
CONFIG_PATH      = os.path.join(T2CHESS_DIR_PATH, 'config.cfg')


API            = None
LASTID         = None
LASTID_PATH    = None
CHECK_INTERVAL = 30 # check every 30 seconds by default


def explain_config():
    print >>sys.stderr, \
"""Create a directory %(dir)s with the following files:
    * config.cfg that must constain directive for program work
    Example:
        [keys]
        APP_KEY = twitter-app-key
        APP_SECRET = twitter-app-secret
        ACCOUNT_KEY = account-key
        ACCOUNT_SECRET = account-secret

        [config]
        msgid-file = file-name
        check-iterval = 30

    Keys holds application and account that communicates with the
    application pair keys provided by twitter and by OAuth
    authentication mechanism.

    Files hods files names used by the application, currently only
    msgid which will contain the last message id retrieved and
    proccesed from twitter account.
""" % {'dir': T2CHESS_DIR_PATH}


def init():
    """Reads configuration and initializes twitter connection"""
    if not os.path.isdir(T2CHESS_DIR_PATH) or not os.path.isfile(CONFIG_PATH):
        explain_config()
        sys.exit(1)

    global API, CHECK_INTERVAL, LASTID, LASTID_PATH

    config = ConfigParser()
    config.read(CONFIG_PATH)

    try: # read config (keys and paths)
        app_key = config.get('keys', 'APP_KEY')
        app_secret = config.get('keys', 'APP_SECRET')
        acc_key = config.get('keys', 'ACCOUNT_KEY')
        acc_secret = config.get('keys', 'ACCOUNT_SECRET')
        LASTID_PATH = config.get('config', 'msgid-file')
    except NoOptionError, e:
        explain_config()
        print >>sys.stderr, e.message
        sys.exit(1)
    
    try: # override check interval time
        CHECK_INTERVAL = int(config.get('config', 'check-interval'))
    except (ValueError, NoOptionError):
        pass

    # read last message id retrieved or None to start from beggining
    try:
        with open(LASTID_PATH, 'r') as fobj:
            try:
                LASTID = int(fobj.readline())
            except ValueError:
                LASTID = None
    except IOError: # file does not exist
        open(LASTID_PATH, 'w').close()
        LASTID = None

    auth = tweepy.OAuthHandler(app_key, app_secret)
    auth.set_access_token(acc_key, acc_secret)
    API = tweepy.API(auth)
    return API


def store_lastid(message):
    """Stores last message id in LASTID_PATH file and in LASTID variable"""
    global LASTID_PATH, LASTID
    LASTID = message.id
    with open(LASTID_PATH, 'w') as fobj:
        fobj.writelines([str(message.id)])



# Messages supported format
#   new           (new game)
#   new @user2    (new game)
#   end           (surrender)
#   draw          (offer draw)
#   *             (anything else is interpreted as a move)
#
# Example:
#       User                              T2Chess
#       @t2chess new           -------->
#                              <--------  @user game started, whites move first,
#                                         check the board here http://.../fen #gameid
#       @t2chess a4 #gameid    -------->
#                              <--------  @user e5, check the board here http://.../fen
#                                         #gameid

def process_message(msg):
    print '    %s: %s (%s)' % (msg.user.name, msg.text, msg.id)


def get_messages():
    """Gets messages sent to account and process them."""
    global API, LASTID
    end = False

    while not end:
        try:
            last_id = str(LASTID) or 'no last id'
            print 'Checking for messages > ' + last_id
            for page in tweepy.Cursor(API.mentions, since_id=LASTID).pages():
                for msg in reversed(page):
                    store_lastid(msg)
                    process_message(msg)
            print 'Checked for messages > ' + last_id
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print 'Interrupted'
            end = True


if __name__ == '__main__':
    init()
    get_messages()
