from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class PokerAgentBase(ABC):
    """Base class that all poker agents must inherit from."""

    DEFAULT_NAME = "Poker Agent"
    STARTING_CHIPS = 100

    def __init__(self, name: Optional[str] = None):
        self.name = name or self.DEFAULT_NAME
        self.chips = self.STARTING_CHIPS
        self._game_state: Optional[Dict[str, Any]] = None

    @abstractmethod
    def make_decision(self, game_state):
        """Return either an action string or a tuple of (action, amount)."""
        raise NotImplementedError

    # --- Turn lifecycle helpers (managed by GameManager) ---
    def _prepare_turn(self, game_state: Dict[str, Any]) -> None:
        """Store the latest game_state so derived agents can use convenience helpers."""
        self._game_state = game_state

    def _finish_turn(self) -> None:
        """Clear the cached game_state after the agent's decision resolves."""
        self._game_state = None

    # --- Convenience accessors ---
    @property
    def state(self) -> Dict[str, Any]:
        """Return the cached game_state, raising if accessed outside a decision."""
        if self._game_state is None:
            raise RuntimeError("Game state is unavailable outside make_decision.")
        return self._game_state

    @property
    def hero(self) -> Dict[str, Any]:
        """Return this agent's public state information."""
        return self.state["self"]

    @property
    def call_required(self) -> int:
        """Amount of chips needed to stay in the hand."""
        return int(self.state.get("call_required", 0))

    @property
    def stack(self) -> int:
        """Convenience alias for remaining chips."""
        return int(self.hero.get("chips", 0))

    # --- Action helpers ---
    def check(self):
        """Select a check action."""
        return "check", 0

    def call(self):
        """Match the current wager, falling back to the remaining stack when short."""
        amount_to_call = self.call_required
        if amount_to_call > self.stack:
            self.debug(
                f"Attempted to call ${amount_to_call} with only ${self.stack}. Folding instead."
            )
            return self.fold()
        return "call", amount_to_call

    def raise_by(self, amount: int):
        """Raise by a specific amount above the call."""
        if amount <= 0:
            self.debug(f"Attempted to raise by a non-positive amount ({amount}).")
        return "raise", amount

    def fold(self):
        """Release the hand without investing further chips."""
        return "fold", 0

    def all_in(self):
        """Move the entire stack into the pot."""
        if self.stack <= 0:
            self.debug("Attempted all-in with no chips remaining.")
        return "all-in", None

    # --- Debug helper ---
    def debug(self, message: str) -> None:
        """Emit a debug statement to standard output for quick diagnostics."""
        print(f"[DEBUG][{self.name}] {message}")
