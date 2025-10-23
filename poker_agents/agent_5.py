"""
Agent 5 — Pushover

Always folds
"""
from poker_agents.agent_base import PokerAgentBase


class PokerAgent(PokerAgentBase):
    DEFAULT_NAME = "Agent 5"

    def __init__(self, name=None):
        super().__init__(name or self.DEFAULT_NAME)

    def make_decision(self, game_state):
        _ = game_state
        return self.fold()
