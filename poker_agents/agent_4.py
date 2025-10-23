# Aggressive ace-aware agent
import random

from poker_agents.agent_base import PokerAgentBase


class PokerAgent(PokerAgentBase):
    DEFAULT_NAME = "Agent 4"

    def __init__(self, name=None):
        super().__init__(name or self.DEFAULT_NAME)

    def make_decision(self, game_state):
        my_state = game_state['self']
        hole_cards = my_state['hole_cards']
        has_ace = any(card.rank == "A" for card in hole_cards)
        call_required = game_state['call_required']
        chips = my_state['chips']

        if has_ace and chips > 0:
            if call_required >= chips:
                return "call", chips
            shove_amount = chips - call_required
            return "raise", max(1, shove_amount)

        if call_required == 0:
            return "check", 0

        if random.random() < 0.5:
            return ("call", call_required) if call_required <= chips else ("fold", 0)

        return ("check", 0) if call_required == 0 else ("fold", 0)
