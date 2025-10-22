# Random poker agent implementation
import random


class PokerAgent:
    def __init__(self, name="Agent 4"):
        self.name = name
        self.chips = 1000
    
    def make_decision(self, game_state):
        """Make a random poker decision"""
        # Get current player info
        current_player = None
        for player in game_state['players']:
            if player.name == self.name:
                current_player = player
                break
        
        if not current_player or current_player.is_folded:
            return "fold", 0
        
        # Random action selection with weights
        current_bet = game_state['current_bet']
        player_bet = current_player.current_bet
        
        if current_bet == player_bet:
            # No bet to call, can only check, fold, or raise
            actions = ["fold", "check", "raise"]
            weights = [0.1, 0.4, 0.5]  # Favor check/raise over fold
        else:
            # There's a bet to call
            actions = ["fold", "call", "raise"]
            weights = [0.2, 0.4, 0.4]  # Favor call/raise over fold
        
        action = random.choices(actions, weights=weights)[0]
        amount = 0
        
        if action == "raise":
            # Random raise amount between 50 and min(200, player.chips)
            max_raise = min(200, current_player.chips)
            if max_raise >= 50:
                amount = random.randint(50, max_raise)
            else:
                # If player can't raise minimum, bet all their chips
                amount = current_player.chips
        elif action == "call":
            # Calculate call amount - bet all chips if can't meet the call
            call_amount = current_bet - player_bet
            amount = min(call_amount, current_player.chips)
        
        return action, amount
