"""
Agent 6 — Cautious Agent

Will raise a small amount of money but will never match a call if it is more than half of its current chips.
"""
from poker_agents.agent_base import PokerAgentBase


class PokerAgent(PokerAgentBase):
    DEFAULT_NAME = "Agent 6"

    def __init__(self, name=None):
        super().__init__(name or self.DEFAULT_NAME)

    def make_decision(self, game_state):
        _ = game_state

        stack = self.stack
        call_required = self.call_required

        if stack <= 0:
            return self.fold()

        half_stack = stack / 2
        if call_required > half_stack:
            return self.fold()

        max_raise = max(1, int(half_stack))

        if call_required == 0:
            raise_amount = min(max(1, int(stack * 0.1)), max_raise)
            return self.raise_by(raise_amount)

        remaining_after_call = stack - call_required
        if remaining_after_call > 0:
            raise_amount = max(
                1,
                min(call_required, remaining_after_call, max_raise)
            )
            if raise_amount > 0:
                return self.raise_by(raise_amount)

        return self.call()
