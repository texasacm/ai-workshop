# Passive checking agent
from poker_agents.agent_base import PokerAgentBase


class PokerAgent(PokerAgentBase):
    DEFAULT_NAME = "Agent 3"

    def __init__(self, name=None):
        super().__init__(name or self.DEFAULT_NAME)

    def make_decision(self, game_state):
        my_state = game_state['self']
        call_required = game_state['call_required']
        chips = my_state['chips']

        if call_required == 0:
            return "check", 0

        if call_required <= chips:
            return "call", call_required

        return "fold", 0
