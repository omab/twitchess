from engines.utils import SubProcess


class ChessEngine(object):
    """Simple Chess Engine Protocol (tm) ;)."""
    def __init__(self, path, args=None):
        """Inits process"""
        self.process = SubProcess(path, args)

    def move(self, pos):
        """Move method."""
        raise NotImplementedError

    def display(self):
        """Display method."""
        raise NotImplementedError

    def new(self):
        """Starts a new game."""
        raise NotImplementedError

    def name(self, name):
        """Set users name."""
        raise NotImplementedError

    def end(self):
        """Ends game."""
        self.process.kill()

    def write(self, msg, flush=False):
        """Write msg to process"""
        self.process.write(msg, flush)

    def read(self):
        """Reads process output"""
        return self.process.read()

    def clear(self):
        """Simulates a clear on process output"""
        self.process.flush()

    def expect(self, regex_mapping):
        """
        Reads until data matches expressiong.

        @regex_mapping is a tuples list which contanins
            (regex_expression, function)
        if regex_expression matches read content, then function
        is invoked and it's valued returned back.
        """
        while self.process.is_alive():
            lines = self.read()
            if lines:
                for regex, func in regex_mapping:
                    result = filter(regex.findall, lines)
                    if result:
                        return func(result)
