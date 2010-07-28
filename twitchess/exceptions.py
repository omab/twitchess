class GameError(Exception):
    """Base game error exception"""

class GameExistsError(GameError):
    """A game already exists"""

class InvalidMove(GameError):
    """Move was invalid"""

class UnknowError(GameError):
    """An unknow error has ocurred"""
