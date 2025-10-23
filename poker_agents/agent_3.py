"""
Agent 3 — Passive Checking Strategy

This agent will always check if possible. Otherwise, it will call to match
"""
from poker_agents.agent_base import PokerAgentBase


class PokerAgent(PokerAgentBase):
    DEFAULT_NAME = "Agent 3"

    def __init__(self, name=None):
        super().__init__(name or self.DEFAULT_NAME)

    def make_decision(self, game_state):
        _ = game_state
        call_required = self.call_required
        chips = self.stack

        # Take the free option whenever the action checks through.
        if call_required == 0:
            return self.check()

        # Call when affordable, otherwise surrender the hand.
        if call_required <= chips:
            return self.call()

        return self.fold()
