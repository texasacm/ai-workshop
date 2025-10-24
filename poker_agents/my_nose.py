"""
Template poker agent.

Copy this file, rename it, and fill in the decision logic.
"""
from typing import Optional, Tuple
import random

from poker_agents.agent_base import PokerAgentBase


class PokerAgent(PokerAgentBase):
    """
    Example agent implementation.

    Agents receive a restricted game_state dictionary with:
      - self: your visible state (chips, hole_cards, current_bet, total_bet, is_all_in)
      - community_cards: community cards that have been revealed
      - pot: current size of the shared pot
      - current_bet: table-wide bet you must match to stay in the hand
      - call_required: how many chips you must commit to call
      - game_phase: one of 'preflop', 'flop', 'turn', 'river', 'showdown'
      - other_player_moves: list of dicts with each opponent's name and last action
      - previous_player_action: the name/action of the player who acted immediately before you
    Agents must return either a string action ('fold', 'check', 'call', 'raise')
    or a tuple of (action, amount) for raises/calls.

    Convenience helpers available during make_decision:
      - self.state / self.hero for quick access to the cached game state
      - self.call_required / self.stack for numeric shortcuts
      - self.check(), self.call(), self.raise_by(amount), self.all_in()
        which emit properly formatted actions for the GameManager
    """

    DEFAULT_NAME = "My Nose"

    def __init__(self, name: Optional[str] = None):
        super().__init__(name or self.DEFAULT_NAME)

    def make_decision(self, game_state) -> Tuple[str, int]:
        _ = game_state  # Access the cached state via helpers to keep code tidy.
        call_required = self.call_required
        chips = self.stack

        r = random.randint(0, 1000)
        if r == 1:
            return self.all_in()

        for card in self.hole_cards:
            if card in _.community_cards:
                if (_.current_bet > self.chips//2):
                    return self.all_in()
                else:
                    return self.raise_by(abs(self.chips//2 - _.current_bet))

        # # --- Replace the logic below with your strategy ---
        # if call_required == 0:
        #     return self.check()

        # if call_required <= max(1, chips // 10):
        #     return self.call()

        # Fold when the call is too expensive
        return self.fold()
