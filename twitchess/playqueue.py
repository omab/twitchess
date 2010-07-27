from threading import Thread

from Queue import Queue, Empty

from twitchess.exceptions import GameExistsError, GameError, InvalidMove
from twitchess.engines.gnuchess import GNUChess
#from twitchess.engines.crafty import Crafty


INVALID_MOVE = False


def notify(move):
    """Notifies player of engine move."""
    print '%s in %s' % (move, move.game)


class Move(object):
    """Move class, stores move and response"""
    def __init__(self, game, move, result=None):
        self.game = game
        self.move = move
        self.result = result

    def do_move(self):
        """Passes move to current game"""
        try:
            self.result = self.game.move(self.move)
        except InvalidMove:
            self.result = INVALID_MOVE

    def __str__(self):
        if self.result == INVALID_MOVE:
            return 'Invalid move: %s' % self.move
        else:
            return '%s %s' % (self.move, self.result)

class MovesManager(object):
    def __init__(self, handler):
        self.pending = Queue()
        self.made = Queue()
        self.handler = handler
        self.running = False
        self._in_thread, self._out_thread = None, None

    def add(self, move):
        """Add item to queue to be processing."""
        self.pending.put(move)

    def start(self):
        """Start threads"""
        if not self.running:
            self.running = True
            self._in_thread = Thread(target=self._in)
            self._out_thread = Thread(target=self._out)
            self._in_thread.start()
            self._out_thread.start()

    def end(self):
        """Stop threads"""
        if self.running:
            self.running = False
            self._in_thread.join()
            self._out_thread.join()

    def _out(self):
        """Process engine moves queue."""
        while self.running:
            try:
                self.handler(self.made.get(timeout=1))
            except Empty:
                pass

    def _in(self):
        """Process user moves queue."""
        while self.running:
            try:
                move = self.pending.get(timeout=1)
                move.do_move()
                self.made.put(move)
            except Empty:
                pass


class PlayQueue(object):
    def __init__(self):
        self.games = {}
        self.mm = MovesManager(notify)

    def new(self, name, engine=GNUChess):
        """
        Creates a game for @name and with @engine. Raises GameError if game
        already exists
        """
        if name not in self.games:
            self.games[name] = engine(name=name)
        else:
            raise GameExistsError, '%s is already playing a game' % name

    def move(self, name, move):
        """Passes a move to a game. Raises GameError if game doen't exist"""
        if name in self.games:
            self.mm.add(Move(self.games[name], move))
            self.mm.start()
        else:
            raise GameError, 'No game exists for %s' % name

    def end(self):
        """Ends games and queue."""
        self.mm.end() # end queue
        for game in self.games.itervalues(): # end games
            game.end()
