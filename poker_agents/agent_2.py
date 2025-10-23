# Mimic previous action agent
from poker_agents.agent_base import PokerAgentBase


class PokerAgent(PokerAgentBase):
    DEFAULT_NAME = "Agent 2"

    def __init__(self, name=None):
        super().__init__(name or self.DEFAULT_NAME)

    def make_decision(self, game_state):
        my_state = game_state['self']
        call_required = game_state['call_required']
        chips = my_state['chips']

        previous = game_state.get('previous_player_action')
        if not previous:
            return ("check", 0) if call_required == 0 else ("fold", 0)

        previous_action = (previous['last_action'] or "").lower()

        if previous_action == "fold":
            return "fold", 0

        if previous_action == "check":
            return ("check", 0) if call_required == 0 else ("fold", 0)

        if previous_action == "call":
            return ("call", call_required) if call_required <= chips else ("fold", 0)

        if previous_action == "raise":
            if chips <= call_required:
                return "fold", 0
            additional = call_required if call_required > 0 else 1
            additional = min(additional, chips - call_required)
            if additional <= 0:
                return "fold", 0
            return "raise", additional

        # Default to matching the pot if possible
        if call_required == 0:
            return "check", 0
        return ("call", call_required) if call_required <= chips else ("fold", 0)
