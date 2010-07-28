import re

from twitchess.engines.base import ChessEngine, raise_invalid_move, \
                                   raise_unknow_error
from twitchess.engines.utils import crafty_board

# binary path and arguments
GNUCHESS = '/usr/games/gnuchess'
GNUCHESS_ARGS = ['-e']

# GNUCHess board:
#     r n b q k b n r 
#     p p p p p p p p 
#     . . . . . . . . 
#     . . . . . . . . 
#     . . . . . . . . 
#     . . . . . . . . 
#     P P P P P P P P 
#     R N B Q K B N R

# regular expressions to detect interesting output
BOARD_RE         = re.compile('^[\.rnbqkpRNBQKP ]+$') # board
ILLEGAL_RE       = re.compile('^Illegal move')        # illegal move
MYMOVE_RE        = re.compile('^My move is')          # machine move
WHITE_PROMPT_RE  = re.compile('^White (\d) :')        # white prompt detection
BLACK_PROMPT_RE  = re.compile('^Black (\d) :')        # black prompt detection


class GNUChess(ChessEngine):
    """GNUChess engine access"""
    def __init__(self, name, pondering=False):
        args = GNUCHESS_ARGS if not pondering else []
        self.prompt_re = WHITE_PROMPT_RE
        super(GNUChess, self).__init__(name, GNUCHESS, args)

    def display(self):
        """Display method."""
        self.write('show board')
        result = self.read()
        return crafty_board(filter(BOARD_RE.match, result))

    def new(self):
        """Starts a new game."""
        self.write('new')

    def end(self):
        """Ends game."""
        self.write('quit')
        super(GNUChess, self).end()

    def do_move(self, pos):
        self.write(pos)
        return self.expect(
            ((MYMOVE_RE, lambda r: r[-1].split(' : ')[-1].strip()),
             (ILLEGAL_RE, raise_invalid_move),
             (self.prompt_re, raise_unknow_error)))
