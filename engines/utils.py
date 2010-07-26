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

    def truncate(self):
        """Truncates buffer to 0 length"""
        self.lock.acquire()
        self.buff = []
        self.lock.release()

    def readlines(self):
        """Reads lines in buffer"""
        self.lock.acquire()

        while not self.buff:
            self.lock.wait()

        result, self.buff = self.buff, []
        self.lock.release()
        return result

    def writelines(self, lines):
        """Writes lines in buffer"""
        self.lock.acquire()
        self.buff.extend(lines)
        self.lock.notify()
        self.lock.release()

def read(subprocess):
    try:
        while subprocess.is_alive():
            yield subprocess.process.stdout.readline()
    except IOError:
        pass
    raise StopIteration


def pipe_reader(subprocess):
    """Reads from subprocess stdout pipe and writes to it's io buffer."""
    while subprocess.is_alive():
        subprocess.process.stdout.flush()
        select([subprocess.process.stdout.fileno()], [], [])
        subprocess.reader.writelines([ line for line in read(subprocess) ])

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

    def flush(self):
        """Flushes stdout. Pipes doesn't support flush, we read until the
        end."""
        self.reader.truncate()

    def write(self, msg, flush=False):
        """Writes msg to process stdin."""
        if flush:
            self.flush()
        self.process.stdin.write(msg + '\n')

    def read(self):
        """Reads process stdout."""
        return self.reader.readlines()

    def kill(self):
        """Kills process"""
        self._process.kill()
        self._reader_thread.join()
        self._reader_thread = None
        self._process = None
