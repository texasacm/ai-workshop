"""
Agent 6 — Cautious Agent

This cautious raiser prefers to apply small pressure but abandons ship if a
raise would cost more than half of the remaining stack. It probes by raising
when affordable, otherwise folding rather than risking too many chips.
"""
from poker_agents.agent_base import PokerAgentBase


class PokerAgent(PokerAgentBase):
    DEFAULT_NAME = "Agent 6"

    def __init__(self, name=None):
        super().__init__(name or self.DEFAULT_NAME)

    def make_decision(self, game_state):
        _ = game_state  # Decision making relies on helper properties.

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
