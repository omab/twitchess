from os.path import sep

from twitchess.exceptions import InvalidMove, UnknowError
from twitchess.engines.utils import SubProcess


INVALID_MOVE, UNKNOW_ERROR = 1, 2


class ChessEngine(object):
    """Simple Chess Engine Protocol (tm) ;)."""
    def __init__(self, name, path, args=None):
        """Inits process"""
        self.is_white = True # engines start with white user by default
        self.name = name
        self.path = path
        self.args = args
        self.moves = []
        self.process = SubProcess(path, args)

    def move(self, pos):
        """Move method. Try to not override this, override do_move
        instead."""
        try:
            result = self.do_move(pos)
        except InvalidMove: # pretify error
            raise InvalidMove, '%s is an invalid move' % pos
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
        raise InvalidMove, 'An invalid move was passed'

    def unknow(self, result):
        raise UnknowError, 'An error has ocurred'

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
            print ''.join(lines)
            for regex, func in regex_mapping:
                result = filter(regex.findall, lines)
                if result:
                    return func(result)

    def __str__(self):
        """Returns name."""
        return '%s vs. %s' % (self.name, self.path.split(sep)[-1])
