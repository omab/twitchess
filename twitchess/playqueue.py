import time
from threading import Thread
from Queue import Queue, Empty

from twitchess.exceptions import GameExistsError, GameError, InvalidMove
from twitchess.engines.gnuchess import GNUChess as DefaultEngine


INVALID_MOVE = False


def print_result(cmd):
    """Prints Command object"""
    print cmd


class Command(object):
    """Representation of an engine command."""
    def __init__(self, game, handler):
        """
        Init method. Details:
            @game       game instance
            @handler    function to invoke on some result
            @result     store result on this attribute
        """
        self.game = game
        self.handler = handler
        self.result = None

    def notify(self):
        """Notify listener"""
        if self.handler and callable(self.handler):
            self.handler(self)

    def execute(self):
        """
        Call engine action and notify after action was ran.

        Note: Do not override this method, instead override do_execute.
        """
        self.do_execute()
        self.notify()

    def do_execute(self):
        """Call engine action. Override in subclasses with needed action."""
        raise NotImplementedError

    def __str__(self):
        """Command str method."""
        return '%s in %s' % (self.result or self.__class__.__name__, self.game)


class Move(Command):
    """Move class, stores move and response"""
    def __init__(self, game, handler, move):
        """
        Init method. Argument details:
            @game       game instance
            @handler    handler to invoke on response
            @move       player move position
        """
        self.move = move
        super(Move, self).__init__(game, handler)

    def do_execute(self):
        """Passes move to current game. Stores engine response in result."""
        try:
            self.result = self.game.move(self.move)
        except InvalidMove:
            self.result = INVALID_MOVE

    def __str__(self):
        """Print move pair (user, engine) or invalid move message."""
        if self.result == INVALID_MOVE:
            return 'Invalid move: %s in %s' % (self.move, self.game)
        else:
            return '%s %s in %s' % (self.move, self.result, self.game)


class Fen(Command):
    """FEN notation command."""
    def do_execute(self):
        """Store FEN string in result."""
        self.result = self.game.fen()

    def __str__(self):
        """Return result."""
        return self.result


class ActionManager(object):
    """
    Asynchronous action manager. Accepts Command objects which passes
    commands to game engines. Works over two queues, one where commands
    are stored before running, and a second where results are proceesed.
    """
    def __init__(self):
        self.pending = Queue()
        self.made = []
        self.running = False
        self._in_thread, self._out_thread = None, None

    def add(self, command):
        """Add item to queue to be processing."""
        if isinstance(command, Command):
            self.pending.put(command)

    def start(self):
        """Start threads"""
        if not self.running:
            self.running = True
            self._in_thread = Thread(target=self._in)
            self._out_thread = Thread(target=self._out)
            self._in_thread.start()
            self._out_thread.start()

    def end(self):
        """Stop threads"""
        if self.running:
            self.running = False
            self._in_thread.join()
            self._out_thread.join()

    def _out(self):
        """Process threads ran or running. Ran threads are joined while
        running are left untouched."""
        while self.running:
            for thread in self.made:
                if not thread.is_alive():
                    thread.join()
            # Use sleep because Conditions or other locking system does't fit
            # well to this purpose
            time.sleep(0.5)

    def _in(self):
        """Process user moves queue."""
        while self.running:
            try: # check for 1 sec and continue if it was empty
                command = self.pending.get(timeout=1)
            except Empty:
                pass
            else:
                thread = Thread(target=command.execute)
                thread.start()
                self.made.append(thread)


class PlayQueue(object):
    def __init__(self):
        self.games = {}
        self.mm = ActionManager()
        self.mm.start()

    def new(self, name, engine=DefaultEngine):
        """
        Creates a game for @name and with @engine. Raises GameError if game
        already exists
        """
        if name not in self.games:
            self.games[name] = engine(name=name)
        else:
            raise GameExistsError, '%s is already playing a game' % name

    def move(self, name, move, notify_handler=print_result):
        """Passes a move to a game."""
        self.command(name, Move, notify_handler, move)

    def fen(self, name, notify_handler=print_result):
        """Passes a move to a game."""
        self.command(name, Fen, notify_handler)

    def command(self, name, CmdClass, notify_handler, *args, **kwargs):
        """Passes a command to a game. Raises GameError if game doen't exist"""
        if name in self.games:
            self.mm.add(CmdClass(self.games[name], notify_handler, *args,
                                 **kwargs))
        else:
            raise GameError, 'No game exists for %s' % name

    def end(self):
        """Ends games and queue."""
        self.mm.end() # end queue
        for game in self.games.itervalues(): # end games
            game.end()
