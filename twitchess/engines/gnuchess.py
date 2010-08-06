import os
import tempfile
import re
import time

from twitchess.engines.base import ChessEngine
from twitchess.engines.utils import crafty_board, parse_move

# binary path and arguments
GNUCHESS = '/usr/games/gnuchess'
GNUCHESS_ARGS = ['-e']

# GNUCHess board:
#     white  KQkq  c6
#     r n b q k b n r 
#     p p p p p p p p 
#     . . . . . . . . 
#     . . . . . . . . 
#     . . . . . . . . 
#     . . . . . . . . 
#     P P P P P P P P 
#     R N B Q K B N R

# regular expressions to detect interesting output
BOARD_RE   = re.compile('^[\.rnbqkpRNBQKP ]+$')           # board
FEN_RE     = re.compile('^[\.rnbqkpRNBQKP1-8a-hwitl ]+$') # full board
ILLEGAL_RE = re.compile('^Illegal move')                  # illegal move
MYMOVE_RE  = re.compile('^My move is')                    # machine move
WHITE_RE   = '^White \(%d\) :'                           # white prompt
BLACK_RE   = '^Black \(%d\) :'                           # black prompt


class GNUChess(ChessEngine):
    """GNUChess engine access"""
    def __init__(self, players, pondering=False):
        args = GNUCHESS_ARGS if not pondering else []
        super(GNUChess, self).__init__(players, GNUCHESS, args)
        if self.multiplayer:
            self.write('manual') # enter manualmode

    def display(self):
        """Reads GNUChess board and converts to ritcher format."""
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

    def fen(self):
        """Reads FEN notation stored in a temporary file saved by GNUChess.
        GNUChess Output format:
            rnbqkbnr/ppp1pppp/8/8/P3p3/8/1PPP1PPP/RNBQKBNR w KQkq - bm 1; id 1;
        Converts to:
            rnbqkbnr/ppp1pppp/8/8/P3p3/8/1PPP1PPP/RNBQKBNR w KQkq - 0 1
        """
        fd, path = tempfile.mkstemp()
        self.write('save ' + path)
        time.sleep(0.5) # some delay :(
        fobj = os.fdopen(fd)
        out = fobj.readline()
        fobj.close()
        os.unlink(path)
        if out:
            out = out.strip().split(';')[0].split()
            out[-2] = '0'
            out = ' '.join(out)
            return out

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
