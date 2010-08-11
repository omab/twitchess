from __future__ import with_statement

import os
import sys
import time
import socket
import simplejson
from os.path import isdir, stat
from optparse import OptionParser

import tweepy

import settings


API    = None
LASTID = None
SOCKET = None


def init(socket=True):
    """Reads configuration and initializes twitter connection"""
    global API, LASTID, SOCKET

    if not isdir(settings.T2CHESS_DIR_PATH):
        print >>sys.stderr, '"%s" is not a directory' % \
                    settings.T2CHESS_DIR_PATH
        sys.exit(1)

    if socket:
        try:
            sstat = os.stat(settings.PLAYQUEUE_SOCKET)
            if sstat.st_mode & stat.S_IFSOCK != stat.S_IFSOCK:
                print >>sys.stderr, '"%s" is not a socket' % \
                            settings.PLAYQUEUE_SOCKET
                sys.exit(1)
        except OSError:
            print >>sys.stderr, '"%s" does not exists' % \
                        settings.PLAYQUEUE_SOCKET
            sys.exit(1)

        SOCKET = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        SOCKET.connect(settings.PLAYQUEUE_SOCKET)

    # read last message id retrieved or None to start from beggining
    try:
        with open(settings.LASTMSGID_FILE, 'r') as fobj:
            try:
                LASTID = int(fobj.readline())
            except ValueError:
                LASTID = None
    except IOError: # file does not exist
        open(settings.LASTMSGID_FILE, 'w').close()
        LASTID = None

    auth = tweepy.OAuthHandler(settings.APP_KEY, settings.APP_SECRET)
    auth.set_access_token(settings.ACCOUNT_KEY, settings.ACCOUNT_SECRET)
    API = tweepy.API(auth)
    return API


def store_lastid(message):
    """Stores last message id in settings.LASTMSGID_FILE file and in LASTID
    variable.
    """
    global LASTID
    LASTID = message.id
    with open(settings.LASTMSGID_FILE, 'w') as fobj:
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
    """Process incoming messages, passes message to playqueue server
    using SOCKET, data sent is JSON."""
    global SOCKET
    print '    %s: %s (%s)' % (msg.user.name, msg.text, msg.id)
    if SOCKET:
        SOCKET.send(simplejson.dumps({'user': msg.user.name,
                                      'msg': msg.text}))


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
            time.sleep(settings.CHECK_INTERVAL)
        except KeyboardInterrupt:
            print 'Interrupted'
            end = True

def end():
    """Closes socket"""
    if SOCKET:
        SOCKET.close()

if __name__ == '__main__':
    parser = OptionParser(usage='%prog [options]')
    parser.add_option('--nosocket', help='Disables socket support', 
                      action='store_false', dest='nosocket',
                      default=True)
    options, args = parser.parse_args()

    init(socket=options.nosocket)
    get_messages()
    end()
