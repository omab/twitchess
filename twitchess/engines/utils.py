from __future__ import with_statement

import os
import fcntl
import threading
from select import select
from subprocess import Popen, PIPE, STDOUT


class Reader(object):
    def __init__(self):
        self.lock = threading.Condition()
        self.buff = []

    def readlines(self):
        """Reads lines in buffer"""
        self.lock.acquire()

        while not self.buff:
            self.lock.wait()

        result, self.buff = self.buff, []
        self.lock.release()
        return result

    def truncate(self):
        """Truncates read data to nothing."""
        self.buff = []

    def writelines(self, lines):
        """Writes lines in buffer"""
        self.lock.acquire()
        self.buff.extend(lines)
        self.lock.notify()
        self.lock.release()


def pipe_reader(subprocess):
    """Reads from subprocess stdout pipe and writes to it's io buffer."""
    def _read(subprocess):
        try:
            while subprocess.is_alive():
                yield subprocess.process.stdout.readline()
        except IOError: # no more data to read
            pass
        raise StopIteration

    fileno = [subprocess.process.stdout.fileno()]
    while subprocess.is_alive():
        select(fileno, [], []) # block until there's something to read
        subprocess.reader.writelines([line for line in _read(subprocess)])

class SubProcess(object):
    """Chess engine base class"""
    def __init__(self, path, args=None):
        """Subprocess initialization.
        Starts @path with arguments @args as a subprocess.
        Starting is delayed until an IO request is issues,
        """
        self.command = [path] + (args or [])
        self.reader = Reader()
        self._process = None
        self._reader_thread = None

    def is_alive(self):
        """Returns true/false according to process live status."""
        return self._process and self._process.poll() == None

    @property
    def process(self):
        """
        Returns current process.

        Starts subprocess if not started, std{in,out,err} are redirected
        to pipes and stdout is set to nonblocking IO.
        """
        if self._process is None:
            process = Popen(self.command, stdin=PIPE, stdout=PIPE,
                            stderr=STDOUT)
            # set non-blocking IO mode to stdout
            fd = process.stdout.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
            self._process = process

            # starts reader thread
            thread = threading.Thread(target=pipe_reader, name='pipe reader',
                                      args=(self,))
            thread.start()
            self._reader_thread = thread
        return self._process

    def write(self, msg):
        """Writes msg to process stdin."""
        self.process.stdin.write(msg + '\n')

    def read(self):
        """Reads process stdout."""
        return self.reader.readlines()

    def truncate(self):
        """Truncate read data."""
        self.reader.truncate()

    def kill(self):
        """Kills process"""
        self._process.kill()
        self._reader_thread.join()
        self._reader_thread = None
        self._process = None


def parse_move(value):
    """Parses result string usually used by GNUChess and Crafty to get move.
    Examples:
        GNUChess: Black (12) : e3
        Crafty: Black(12): e3
    """
    return value[-1].split(':')[-1].strip()


def crafty_board(lines):
    """Convert simple chess board (like GNUChess) to Crafty richer format."""
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
