import re

from engines.base import ChessEngine


# binary path
CRAFTY = '/usr/games/crafty'

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
ILLEGAL_RE = re.compile('^Illegal move')                     # illegal move
MYMOVE_RE  = re.compile('Black\(\d+\): [RNBQKP]?[a-h][1-8]') # maching move


class Crafty(ChessEngine):
    """GNU Chess engine access"""
    def __init__(self, pondering=False):
        super(Crafty, self).__init__(CRAFTY)
        self.write('ponder ' + ('on' if pondering else 'off'))
        self.write('noise 937459712')

    def display(self):
        """Display method."""
        self.write('display', flush=True)
        print ''.join(line[4:] for line in filter(BOARD_RE.match, self.read()))

    def new(self):
        """Starts a new game."""
        self.write('new')

    def name(self, name):
        """Set users name."""
        if name:
            self.write('name ' + name)

    def end(self):
        """Ends game."""
        self.write('end')
        super(Crafty, self).end()

    def move(self, pos):
        self.clear()
        self.write(pos)
        return self.expect(
            ((MYMOVE_RE, lambda r: r[-1].split(': ')[-1].strip()),
             (ILLEGAL_RE, lambda r: False)))
