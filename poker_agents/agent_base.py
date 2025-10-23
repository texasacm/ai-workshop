from abc import ABC, abstractmethod
from typing import Optional


class PokerAgentBase(ABC):
    """Base class that all poker agents must inherit from."""

    DEFAULT_NAME = "Poker Agent"
    STARTING_CHIPS = 100

    def __init__(self, name: Optional[str] = None):
        self.name = name or self.DEFAULT_NAME
        self.chips = self.STARTING_CHIPS

    @abstractmethod
    def make_decision(self, game_state):
        """Return either an action string or a tuple of (action, amount)."""
        raise NotImplementedError
