import re

from twitchess.engines.base import ChessEngine
from twitchess.engines.utils import crafty_board, parse_move

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
BOARD_RE   = re.compile('^[\.rnbqkpRNBQKP ]+$')     # board
ILLEGAL_RE = re.compile('^Illegal move')            # illegal move
MYMOVE_RE  = re.compile('^My move is')              # machine move
PROMPT_RE  = re.compile('^(White|Black) \(\d+\) :') # prompt


class GNUChess(ChessEngine):
    """GNUChess engine access"""
    def __init__(self, name, pondering=False):
        args = GNUCHESS_ARGS if not pondering else []
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
        return self.expect(((MYMOVE_RE, parse_move),
                            (ILLEGAL_RE, self.illegal),
                            (PROMPT_RE, self.unknow)))
