"""
Agent 4 — Ace-Aware Aggressor

This semi-bluffing bot jams all-in whenever it holds an ace. Without that
high card it controls the pot size, mixing in occasional calls while favouring
checks or folds to preserve chips.
"""
import random

from poker_agents.agent_base import PokerAgentBase


class PokerAgent(PokerAgentBase):
    DEFAULT_NAME = "Agent 4"

    def __init__(self, name=None):
        super().__init__(name or self.DEFAULT_NAME)

    def make_decision(self, game_state):
        _ = game_state  # Helper methods expose the relevant state.
        hole_cards = self.hero['hole_cards']
        has_ace = any(card.rank == "A" for card in hole_cards)
        call_required = self.call_required
        chips = self.stack

        # With an ace in hand, crank up the pressure and shove when possible.
        if has_ace and chips > 0:
            return self.all_in()

        # No ace: prefer pot control via checks when given the option.
        if call_required == 0:
            return self.check()

        # Mix in some loose calls to add stochastic aggression.
        if random.random() < 0.5:
            return self.call() if call_required <= chips else self.fold()

        return self.fold()
