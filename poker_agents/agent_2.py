"""
Agent 2 — Copycat

This agent will mimic the previous agent's move
"""
from poker_agents.agent_base import PokerAgentBase


class PokerAgent(PokerAgentBase):
    DEFAULT_NAME = "Agent 2"

    def __init__(self, name=None):
        super().__init__(name or self.DEFAULT_NAME)

    def make_decision(self, game_state):
        _ = game_state
        call_required = self.call_required
        chips = self.stack

        previous = self.state.get('previous_player_action')
        # Without history we default to the safest option available.
        if not previous:
            return self.check() if call_required == 0 else self.fold()

        previous_action = (previous['last_action'] or "").lower()

        # Stay out of trouble when the previous player already bailed.
        if previous_action == "fold":
            return self.fold()

        if previous_action == "check":
            return self.check() if call_required == 0 else self.fold()

        if previous_action == "call":
            return self.call() if call_required <= chips else self.fold()

        if previous_action == "raise":
            if chips <= call_required:
                return self.fold()
            additional = call_required if call_required > 0 else 1
            additional = min(additional, chips - call_required)
            if additional <= 0:
                return self.fold()
            # Try to keep the raise alive by matching the wager size.
            return self.raise_by(additional)

        # Default to matching the pot if possible
        if call_required == 0:
            return self.check()
        return self.call() if call_required <= chips else self.fold()
