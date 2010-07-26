import re

from engines.base import ChessEngine


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
BOARD_RE   = re.compile('^[\.rnbqkpRNBQKP ]+$') # board
ILLEGAL_RE = re.compile('^Illegal move')        # illegal move
MYMOVE_RE  = re.compile('^My move is')          # machine move


def crafty_board(lines):
    """Convert GNUChess simple board to Crafty richer format."""
    row_sep = '   +---+---+---+---+---+---+---+---+'
    board = [
        ['8  ', '   ', ' . ', '   ', ' . ', '   ', ' . ', '   ', ' . '],
        ['7  ', ' . ', '   ', ' . ', '   ', ' . ', '   ', ' . ', '   '],
        ['6  ', '   ', ' . ', '   ', ' . ', '   ', ' . ', '   ', ' . '],
        ['5  ', ' . ', '   ', ' . ', '   ', ' . ', '   ', ' . ', '   '],
        ['4  ', '   ', ' . ', '   ', ' . ', '   ', ' . ', '   ', ' . '],
        ['3  ', ' . ', '   ', ' . ', '   ', ' . ', '   ', ' . ', '   '],
        ['2  ', '   ', ' . ', '   ', ' . ', '   ', ' . ', '   ', ' . '],
        ['1  ', ' . ', '   ', ' . ', '   ', ' . ', '   ', ' . ', '   ']
    ]

    for row, line in enumerate(lines):
        for col, char in enumerate(line.replace(' ', '')):
            if char.lower() in 'rnbqkp':
                if char in 'rnbqkp':
                    char = '<' + char.upper() + '>'
                elif char in 'RNBQKP':
                    char = '-' + char + '-'
                # avoid first col in board which is row number
                board[row][col + 1] = char

    return row_sep + '\n' + ('\n' + row_sep + '\n').join(
            ['|'.join(row) + '|' for row in board] +
            ['     a   b   c   d   e   f   g   h  '])


class GNUChess(ChessEngine):
    """GNU Chess engine access"""
    def __init__(self, pondering=False):
        args = GNUCHESS_ARGS if not pondering else []
        super(GNUChess, self).__init__(GNUCHESS, args)

    def display(self):
        """Display method."""
        self.write('show board', flush=True)
        result = self.read()
        print crafty_board(filter(BOARD_RE.match, result))

    def new(self):
        """Starts a new game."""
        self.write('new')

    def name(self, name):
        """Set users name."""
        if name:
            self.write('name ' + name)

    def end(self):
        """Ends game."""
        self.write('quit')
        super(GNUChess, self).end()

    def move(self, pos):
        self.clear()
        self.write(pos)
        return self.expect(
            ((MYMOVE_RE, lambda r: r[-1].split(' : ')[-1].strip()),
             (ILLEGAL_RE, lambda r: False)))
