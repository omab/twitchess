from os.path import sep

from twitchess.exceptions import InvalidMove, UnknowError
from twitchess.engines.utils import SubProcess


class ChessEngine(object):
    """Simple Chess Engine Protocol (tm) ;)."""
    def __init__(self, players, path, args=None):
        """Inits process"""
        self.is_white = True # engines start with white user by default
        if not isinstance(players, tuple):
            self.multiplayer = False # single player mode
            players = (players, None)
        else:
            self.multiplayer = True # multiplayer mode
        self.white, self.black = players
        self.turn = self.white
        self.path = path
        self.args = args
        self.moves = []
        self.process = SubProcess(path, args)

    def is_white_turn(self):
        """Return if next move corresponds to white player"""
        return self.turn == self.white

    def is_black_turn(self):
        """Return if next move corresponds to black player"""
        return self.turn == self.black

    def next_turn(self):
        """Switch turns"""
        self.turn = self.black if self.is_white_turn() else self.white

    def move(self, pos):
        """Move method. Try to not override this, override do_move
        instead."""
        try:
            result = self.do_move(pos)
        except InvalidMove: # pretify error
            raise InvalidMove, '%s is an invalid move' % pos

        if self.multiplayer:
            if self.is_white_turn():
                self.moves.append((pos, None))
            else:
                self.moves[-1] = (self.moves[-1][0], None)
            self.next_turn()
        else:
            self.moves.append((pos, result))
        return result

    def do_move(self, pos):
        """Move method. Return engine result or return False on invalid
        move or error."""
        raise NotImplementedError

    def display(self):
        """Display method."""
        raise NotImplementedError

    def new(self):
        """Starts a new game."""
        raise NotImplementedError

    def end(self):
        """Ends game."""
        self.process.kill()

    def write(self, msg, truncate=True):
        """Write msg to process"""
        if truncate:
            self.process.truncate()
        self.process.write(msg)

    def read(self):
        """Reads process output"""
        return self.process.read()

    def fen(self):
        """Returns FEN notation for current board."""
        raise NotImplementedError

    def illegal(self, result):
        """InvalidMove handler for expect function."""
        raise InvalidMove, 'An invalid move was passed'

    def unknow(self, result):
        """UnknowError handler for expect function."""
        raise UnknowError, 'An error has ocurred'

    def noop(self, result):
        """No operation handler for expect function."""
        pass

    def expect(self, regex_mapping):
        """
        Reads until data matches expressiong.

        @regex_mapping is a tuples list which contanins
            (regex_expression, function)
        if regex_expression matches read content, then function
        is invoked and it's valued returned back.
        """
        while self.process.is_alive():
            lines = self.read()
            for regex, func in regex_mapping:
                result = filter(regex.findall, lines)
                if result:
                    return func(result)

    def __str__(self):
        """User friendly string representantion."""
        if self.white and self.black:
            return '%s vs. %s' % (self.white, self.black)
        else:
            return '%s vs. %s' % (self.white, self.path.split(sep)[-1])
