import re

from twitchess.exceptions import GameError
from twitchess.engines.base import ChessEngine
from twitchess.engines.utils import parse_move


# binary path
CRAFTY      = '/usr/games/crafty'

# Crafty board:
#        +---+---+---+---+---+---+---+---+
#     8  |<R>|<N>|<B>|<Q>|<K>|<B>|   |<R>|
#        +---+---+---+---+---+---+---+---+
#     7  |<P>|<P>|<P>|<P>|<P>|<P>|<P>|<P>|
#        +---+---+---+---+---+---+---+---+
#     6  |   | . |   | . |   |<N>|   | . |
#        +---+---+---+---+---+---+---+---+
#     5  | . |   | . |   | . |   | . |   |
#        +---+---+---+---+---+---+---+---+
#     4  |   | . |   |-P-|   | . |   | . |
#        +---+---+---+---+---+---+---+---+
#     3  | . |   | . |   | . |   | . |   |
#        +---+---+---+---+---+---+---+---+
#     2  |-P-|-P-|-P-| . |-P-|-P-|-P-|-P-|
#        +---+---+---+---+---+---+---+---+
#     1  |-R-|-N-|-B-|-Q-|-K-|-B-|-N-|-R-|
#        +---+---+---+---+---+---+---+---+
#          a   b   c   d   e   f   g   h

# regular expressions to detect interesting output
BOARD_RE   = re.compile('^[ \|1-8<>\+\-a-h\.RNBQKP]+$')      # board
FEN_RE     = re.compile('^setboard .*')                      # FEN
ILLEGAL_RE = re.compile('^Illegal move')                     # illegal
MYMOVE_RE  = re.compile('Black\(\d+\): [RNBQKP]?[a-h][1-8]') # maching
WHITE_RE   = '^White\(%d\):'                                 # white prompt
BLACK_RE   = '^Black\(%d\):'                                 # black prompt


class Crafty(ChessEngine):
    """Crafty chess engine access"""
    def __init__(self, players, pondering=False):
        super(Crafty, self).__init__(players, CRAFTY)
        if self.multiplayer:
            raise GameError, 'multiplayer not supported by Crafty yet'
        # Disable log files (game.xxx and log.xxx files)
        self.write('log off')
        # Disable noise as much as possible while thinking engine move
        # noice <big number> will disable maching thinking noise for a lot of
        # time until level reaches is too deep (something that can happen on
        # advanced games)
        self.write('noise 937459712')
        # Disable pondering
        # Disables thinking on player time. What? who said it was a fair game?
        if not pondering:
            self.write('ponder off')

    def display(self):
        """Display method."""
        self.write('display')
        return ''.join(line[4:] for line in filter(BOARD_RE.match,
                                                   self.read()))

    def new(self):
        """Starts a new game."""
        self.write('new')

    def end(self):
        """Ends game."""
        self.write('end')
        super(Crafty, self).end()

    def fen(self):
        """Reads FEN notation from Crafty. Appends completes moves at end."""
        self.write('savepos')
        prompt = re.compile((WHITE_RE if self.is_white_turn() else BLACK_RE) %
                                    (len(self.moves) + 1,))

        out = self.expect(((FEN_RE, lambda result: result),
                           (ILLEGAL_RE, self.illegal),
                           (prompt, self.unknow)))
        if out:
            moves = ' 0 %d' % len(self.moves)
            return out[0].replace('setboard ', '').replace('\n', '') + moves

    def do_move(self, pos):
        # regular expression to detect prompt, adds 2 becuse it's 1-indexed
        prompt = re.compile((WHITE_RE if self.is_white_turn() else BLACK_RE) %
                                    (len(self.moves) + 2,))

        if self.multiplayer:
            expect = [(ILLEGAL_RE, self.illegal), # user introduced an illegal move
                      (prompt, self.noop)] # prompt reached
        else:
            expect = [(MYMOVE_RE, parse_move), # engine move
                      (ILLEGAL_RE, self.illegal), # user introduced an illegal move
                      (prompt, self.unknow)] # prompt reached without result

        self.write(pos) # write player move
        return self.expect(expect)
