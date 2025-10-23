"""
Agent 4 — Ace Lover

Goes all in with an ace, checks otherwise. If call is required, call with 50% probability, otherwise it folds.
"""
import random

from poker_agents.agent_base import PokerAgentBase


class PokerAgent(PokerAgentBase):
    DEFAULT_NAME = "Agent 4"

    def __init__(self, name=None):
        super().__init__(name or self.DEFAULT_NAME)

    def make_decision(self, game_state):
        _ = game_state
        hole_cards = self.hero['hole_cards']
        has_ace = any(card.rank == "A" for card in hole_cards)
        call_required = self.call_required
        chips = self.stack

        # Go all in if has an ace
        if has_ace and chips > 0:
            return self.all_in()

        # Check when no ace
        if call_required == 0:
            return self.check()

        # Randomly calls or folds
        if random.random() < 0.5:
            return self.call() if call_required <= chips else self.fold()

        return self.fold()
