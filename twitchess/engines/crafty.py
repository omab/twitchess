import re

from twitchess.engines.base import ChessEngine, raise_invalid_move, \
                                   raise_unknow_error


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
BOARD_RE         = re.compile('^[ \|1-8<>\+\-a-h\.RNBQKP]+$')      # board
# moves
ILLEGAL_RE       = re.compile('^Illegal move')                     # illegal
MYMOVE_RE        = re.compile('Black\(\d+\): [RNBQKP]?[a-h][1-8]') # maching
# prompts
WHITE_PROMPT_RE  = re.compile('^White(\d):') # white prompt detection
BLACK_PROMPT_RE  = re.compile('^Black(\d):') # black prompt detection


class Crafty(ChessEngine):
    """Crafty chess engine access"""
    def __init__(self, name, pondering=False):
        super(Crafty, self).__init__(name, CRAFTY)
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
        self.prompt_re = WHITE_PROMPT_RE

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

    def do_move(self, pos):
        self.write(pos)
        return self.expect(
            ((MYMOVE_RE, lambda r: r[-1].split(': ')[-1].strip()),
             (ILLEGAL_RE, raise_invalid_move),
             (self.prompt_re, raise_unknow_error)))
