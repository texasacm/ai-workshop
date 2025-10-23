"""
Template poker agent.

Copy this file, rename it, and fill in the decision logic.
"""
from typing import Optional, Tuple

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
    """

    DEFAULT_NAME = "Template Agent"

    def __init__(self, name: Optional[str] = None):
        super().__init__(name or self.DEFAULT_NAME)

    def make_decision(self, game_state) -> Tuple[str, int]:
        my_state = game_state["self"]
        chips = my_state["chips"]
        call_required = game_state["call_required"]

        # game_state reference:
        #   self -> {'chips', 'hole_cards', 'current_bet', 'total_bet', 'is_all_in'}
        #   community_cards -> list of Card objects everyone can see
        #   pot -> total chips in the middle
        #   current_bet -> highest bet any player has committed this round
        #   call_required -> how many chips you must put in to call
        #   game_phase -> preflop / flop / turn / river / showdown
        #   other_player_moves -> [{'name', 'last_action'} for opponents]
        #   previous_player_action -> {'name', 'last_action'} for the last actor (or None)

        # --- Replace the logic below with your strategy ---
        if call_required == 0:
            return "check", 0

        if call_required <= chips // 10:
            return "call", call_required

        # Fold when the call is too expensive
        return "fold", 0
