import os
import sys
import importlib.util
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import random
from enum import Enum
import time

class Suit(Enum):
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"

class Card:
    def __init__(self, rank: str, suit: Suit):
        self.rank = rank
        self.suit = suit
    
    def __str__(self):
        return f"{self.rank} of {self.suit.value}"
    
    def __repr__(self):
        return f"Card({self.rank}, {self.suit.value})"
    
    def get_value(self):
        """Get numeric value for comparison"""
        if self.rank == 'A':
            return 14
        elif self.rank == 'K':
            return 13
        elif self.rank == 'Q':
            return 12
        elif self.rank == 'J':
            return 11
        else:
            return int(self.rank)

class Player:
    def __init__(self, name: str, chips: int = 1000, agent=None):
        self.name = name
        self.chips = chips
        self.hole_cards = []
        self.current_bet = 0
        self.total_bet = 0
        self.is_folded = False
        self.is_all_in = False
        self.agent = agent
        self.position = 0
        self.last_action = None
    
    def add_card(self, card: Card):
        self.hole_cards.append(card)
    
    def clear_cards(self):
        self.hole_cards = []
    
    def bet(self, amount: int) -> bool:
        if amount > self.chips:
            return False
        self.chips -= amount
        self.current_bet += amount
        self.total_bet += amount
        if self.chips == 0:
            self.is_all_in = True
        return True
    
    def fold(self):
        self.is_folded = True
        self.hole_cards = []
    
    def reset_for_new_hand(self):
        self.current_bet = 0
        self.total_bet = 0
        self.is_folded = False
        self.is_all_in = False
        self.clear_cards()

class GameState:
    def __init__(self):
        self.players = []
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.dealer_position = 0
        self.current_player = 0
        self.game_phase = "preflop"  # preflop, flop, turn, river, showdown
        self.deck = []
        self.winner = None
        self.pending_players = set()
        
    def reset_deck(self):
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        suits = [Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS, Suit.SPADES]
        self.deck = [Card(rank, suit) for rank in ranks for suit in suits]
        random.shuffle(self.deck)
    
    def deal_card(self) -> Card:
        if self.deck:
            return self.deck.pop()
        return None

class GameManager:
    def __init__(self, move_interval: float = 1.0):
        self.game_state = GameState()
        self.gui = None
        self.move_interval = move_interval
        self.load_agents()
    
    def load_agents(self):
        """Load poker agents from the poker_agents folder"""
        agents_folder = "poker_agents"
        if not os.path.exists(agents_folder):
            print(f"Warning: {agents_folder} folder not found")
            return
        
        agent_files = [f for f in os.listdir(agents_folder) if f.endswith('.py')]
        
        for i, agent_file in enumerate(agent_files[:8]):  # Max 8 players
            try:
                spec = importlib.util.spec_from_file_location(
                    f"agent_{i}", 
                    os.path.join(agents_folder, agent_file)
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Try to instantiate the agent
                if hasattr(module, 'PokerAgent'):
                    agent = module.PokerAgent(f"Agent {i+1}")
                    player = Player(f"Agent {i+1}", 1000, agent)
                    player.position = i
                    self.game_state.players.append(player)
                else:
                    # Create a default player if no PokerAgent class found
                    player = Player(f"Agent {i+1}", 1000)
                    player.position = i
                    self.game_state.players.append(player)
                    
            except Exception as e:
                print(f"Error loading {agent_file}: {e}")
                # Create a default player on error
                player = Player(f"Agent {i+1}", 1000)
                player.position = i
                self.game_state.players.append(player)
    
    def start_new_hand(self):
        """Start a new poker hand"""
        self.game_state.reset_deck()
        self.game_state.community_cards = []
        self.game_state.pot = 0
        self.game_state.current_bet = 0
        self.game_state.winner = None
        
        # Reset only active players (those with chips)
        for player in self.game_state.players:
            if player.chips > 0:  # Only reset players who are still in the game
                player.reset_for_new_hand()
        
        # Deal hole cards only to active players
        for _ in range(2):
            for player in self.game_state.players:
                if player.chips > 0 and not player.is_folded:
                    card = self.game_state.deal_card()
                    if card:
                        player.add_card(card)
        
        self.game_state.game_phase = "preflop"
        
        # Find first active player for current player
        self.game_state.current_player = 0
        for i, player in enumerate(self.game_state.players):
            if player.chips > 0:
                self.game_state.current_player = i
                break

        self._reset_pending_players(self.game_state.current_player)
        
        if self.gui:
            self.gui.update_display()
    
    def deal_community_cards(self, count: int):
        """Deal community cards"""
        for _ in range(count):
            card = self.game_state.deal_card()
            if card:
                self.game_state.community_cards.append(card)
        
        if self.gui:
            self.gui.update_display()
    
    def next_phase(self):
        """Move to the next game phase"""
        if self.game_state.game_phase == "preflop":
            self.deal_community_cards(3)
            self.game_state.game_phase = "flop"
        elif self.game_state.game_phase == "flop":
            self.deal_community_cards(1)
            self.game_state.game_phase = "turn"
        elif self.game_state.game_phase == "turn":
            self.deal_community_cards(1)
            self.game_state.game_phase = "river"
        elif self.game_state.game_phase == "river":
            self.game_state.game_phase = "showdown"
        
        # Reset betting for new phase (except showdown)
        if self.game_state.game_phase != "showdown":
            self._reset_betting_round()
        
        if self.gui:
            self.gui.update_display()
    
    def _reset_betting_round(self):
        """Reset betting round for new phase"""
        # Reset current bet and player bets for new betting round
        self.game_state.current_bet = 0
        for player in self.game_state.players:
            if not player.is_folded:
                player.current_bet = 0
                # Keep total_bet for pot calculation
        self._reset_pending_players()

    def player_action(self, player_index: int, action: str, amount: int = 0):
        """Process a player's action"""
        if player_index >= len(self.game_state.players):
            return False
        
        player = self.game_state.players[player_index]
        if player.is_folded or player.is_all_in:
            self.game_state.pending_players.discard(player_index)
            return False

        success = False
        previous_bet = self.game_state.current_bet
        
        if action == "fold":
            player.fold()
            success = True
        elif action == "call":
            call_amount = max(0, self.game_state.current_bet - player.current_bet)
            if call_amount == 0:
                success = True
            else:
                amount_to_call = min(call_amount, player.chips)
                if amount_to_call > 0 and player.bet(amount_to_call):
                    self.game_state.pot += amount_to_call
                    success = True
        elif action == "raise":
            if amount <= 0:
                return False
            call_amount = max(0, self.game_state.current_bet - player.current_bet)
            total_commit = call_amount + amount
            amount_to_bet = min(total_commit, player.chips)
            if amount_to_bet > 0 and player.bet(amount_to_bet):
                self.game_state.pot += amount_to_bet
                success = True
        elif action == "check":
            if self.game_state.current_bet == player.current_bet:
                success = True
        else:
            return False

        if not success:
            return False

        self.game_state.current_bet = max(previous_bet, player.current_bet)

        was_raise = player.current_bet > previous_bet

        if was_raise:
            self.game_state.pending_players = {
                idx for idx in self._players_who_can_act() if idx != player_index
            }
        else:
            self.game_state.pending_players.discard(player_index)

        self._remove_inactive_from_pending()
        
        if self.gui:
            self.gui.update_display()
        
        return True
    
    def evaluate_hand(self, cards: List[Card]) -> Tuple[int, List[int]]:
        """Evaluate a poker hand and return (hand_rank, kickers)"""
        if len(cards) < 5:
            values = sorted([card.get_value() for card in cards], reverse=True)
            return (1 if values else 0, values)
        
        # Get all possible 5-card combinations
        from itertools import combinations
        best_hand = (0, [])
        
        for combo in combinations(cards, 5):
            hand_rank, kickers = self._evaluate_five_cards(list(combo))
            if hand_rank > best_hand[0] or (hand_rank == best_hand[0] and kickers > best_hand[1]):
                best_hand = (hand_rank, kickers)
        
        return best_hand
    
    def _evaluate_five_cards(self, cards: List[Card]) -> Tuple[int, List[int]]:
        """Evaluate a 5-card hand"""
        values = [card.get_value() for card in cards]
        suits = [card.suit for card in cards]
        value_counts = Counter(values)
        sorted_values_desc = sorted(values, reverse=True)
        
        is_flush = len(set(suits)) == 1
        is_straight, straight_high = self._is_straight(values)
        
        count_groups = sorted(
            value_counts.items(),
            key=lambda item: (-item[1], -item[0])
        )
        counts = [count for _, count in count_groups]
        ordered_vals = [val for val, _ in count_groups]
        secondary_count = counts[1] if len(counts) > 1 else 0
        
        if is_flush and is_straight:
            if straight_high == 14 and sorted(values) == [10, 11, 12, 13, 14]:
                return (10, [14])
            return (9, [straight_high])
        
        if counts[0] == 4:
            four = ordered_vals[0]
            kicker = max(v for v in values if v != four)
            return (8, [four, kicker])
        
        if counts[0] == 3 and secondary_count == 2:
            return (7, [ordered_vals[0], ordered_vals[1]])
        
        if is_flush:
            return (6, sorted_values_desc)
        
        if is_straight:
            return (5, [straight_high])
        
        if counts[0] == 3:
            kickers = sorted([v for v in values if v != ordered_vals[0]], reverse=True)
            return (4, [ordered_vals[0]] + kickers)
        
        if counts[0] == 2 and secondary_count == 2:
            high_pair, low_pair = ordered_vals[:2]
            kicker = max(v for v in values if v not in (high_pair, low_pair))
            return (3, [high_pair, low_pair, kicker])
        
        if counts[0] == 2:
            pair = ordered_vals[0]
            kickers = sorted([v for v in values if v != pair], reverse=True)
            return (2, [pair] + kickers)
        
        return (1, sorted_values_desc)
    
    def _is_straight(self, values: List[int]) -> Tuple[bool, int]:
        """Check if values form a straight and return (is_straight, high_card)"""
        unique_values = sorted(set(values))
        if len(unique_values) != 5:
            return False, 0
        
        # Wheel straight (A-2-3-4-5)
        if unique_values == [2, 3, 4, 5, 14]:
            return True, 5
        
        for i in range(4):
            if unique_values[i + 1] - unique_values[i] != 1:
                return False, 0
        
        return True, unique_values[-1]
    
    def determine_winner(self) -> List[Player]:
        """Determine the winner(s) of the current hand"""
        active_players = [p for p in self.game_state.players if not p.is_folded]
        
        if len(active_players) == 1:
            return active_players
        
        # Evaluate each player's best hand
        player_hands = []
        for player in active_players:
            all_cards = player.hole_cards + self.game_state.community_cards
            hand_rank, kickers = self.evaluate_hand(all_cards)
            player_hands.append((player, hand_rank, kickers))
        
        # Sort by hand strength
        player_hands.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        # Find winners (players with the same best hand)
        best_hand = player_hands[0][1:]
        winners = [p[0] for p in player_hands if p[1:] == best_hand]
        
        return winners
    
    def award_pot(self, winners: List[Player]):
        """Award the pot to the winner(s)"""
        if not winners:
            return
        
        share_count = len(winners)
        if share_count == 0:
            return
        
        pot_per_winner = self.game_state.pot // share_count
        remainder = self.game_state.pot % share_count
        
        for i, winner in enumerate(winners):
            amount = pot_per_winner + (1 if i < remainder else 0)
            winner.chips += amount
        
        self.game_state.pot = 0
        self.game_state.pending_players.clear()
    
    def get_random_action(self, player: Player) -> Tuple[str, int]:
        """Get a random action for a player"""
        actions = ["fold", "call", "check", "raise"]
        weights = [0.1, 0.3, 0.3, 0.3]  # Favor call/check/raise over fold
        
        action = random.choices(actions, weights=weights)[0]
        amount = 0
        
        if action == "raise":
            # Random raise amount between 10 and min(100, player.chips)
            max_raise = min(100, player.chips)
            amount = random.randint(10, max_raise)
        elif action == "call":
            # Calculate call amount
            amount = self.game_state.current_bet - player.current_bet
        
        return action, amount
    
    def play_autonomous_round(self):
        """Play one round of autonomous poker"""
        # Check if only one player has chips left
        active_players = [p for p in self.game_state.players if p.chips > 0]
        if len(active_players) <= 1:
            if len(active_players) == 1:
                winner = active_players[0]
                if self.gui:
                    self.gui.log_message(f"🎉 GAME OVER! {winner.name} WINS THE TOURNAMENT! 🎉")
                return False
            else:
                if self.gui:
                    self.gui.log_message("Game ended - no players with chips")
                return False
        
        if self.game_state.game_phase == "showdown":
            # Determine winner and award pot
            winners = self.determine_winner()
            if winners:
                pot_amount = self.game_state.pot  # Store pot amount before awarding
                self.award_pot(winners)
                winner_names = [w.name for w in winners]
                if self.gui:
                    self.gui.log_message(f"Winners: {', '.join(winner_names)} win ${pot_amount}")
            
            # Start a new hand automatically
            self.start_new_hand()
            if self.gui:
                self.gui.log_message("=== NEW HAND DEALT ===")
            return True
        
        # Check if we should progress to next phase
        if self._should_progress_phase():
            self.next_phase()
            if self.gui:
                self.gui.log_message(f"Phase progressed to: {self.game_state.game_phase}")
            return True
        
        # Get current player
        current_player = self.game_state.players[self.game_state.current_player]
        
        # Skip players with no chips
        if current_player.chips <= 0:
            self.next_player()
            return True
        
        if current_player.is_folded or current_player.is_all_in:
            self.next_player()
            return True
        
        # Get random action from agent
        action, amount = self._get_agent_action(current_player)
        
        # Log the action
        if self.gui:
            self.gui.log_message(f"{current_player.name} {action}s" + (f" ${amount}" if amount > 0 else ""))
        
        # Execute action
        success = self.player_action(self.game_state.current_player, action, amount)
        
        # Set last action after successful execution
        if success:
            current_player.last_action = action
        
        if success:
            self.next_player()
        
        return True
    
    def _should_progress_phase(self):
        """Check if we should progress to the next phase"""
        # Count active players
        active_players = [p for p in self.game_state.players if not p.is_folded]
        
        if len(active_players) <= 1:
            return True
        
        if not self.game_state.pending_players:
            return True

    def _get_agent_action(self, player):
        """Get action from player's agent"""
        if player.agent and hasattr(player.agent, 'make_decision'):
            try:
                # Get game state for agent
                game_state = {
                    'players': self.game_state.players,
                    'community_cards': self.game_state.community_cards,
                    'pot': self.game_state.pot,
                    'current_bet': self.game_state.current_bet,
                    'game_phase': self.game_state.game_phase
                }
                action = player.agent.make_decision(game_state)
                if isinstance(action, tuple):
                    return action
                else:
                    return action, 0
            except:
                pass
        
        # Fallback to random action
        return self.get_random_action(player)
    
    def next_player(self):
        """Move to the next active player"""
        if not self.game_state.players:
            return

        total_players = len(self.game_state.players)
        start_index = self.game_state.current_player

        for offset in range(1, total_players + 1):
            candidate = (start_index + offset) % total_players
            candidate_player = self.game_state.players[candidate]

            if candidate_player.is_folded or candidate_player.chips <= 0 or candidate_player.is_all_in:
                continue
            if self.game_state.pending_players and candidate not in self.game_state.pending_players:
                continue

            self.game_state.current_player = candidate
            return

        # Fallback to original player if no valid candidate found
        self.game_state.current_player = start_index

    def _players_who_can_act(self):
        """Return indices of players who can take an action"""
        return [
            idx for idx, player in enumerate(self.game_state.players)
            if not player.is_folded and not player.is_all_in and player.chips > 0
        ]

    def _reset_pending_players(self, starting_index=None):
        """Reset the set of players who still need to act in the current betting round"""
        self.game_state.pending_players = set(self._players_who_can_act())

        if not self.game_state.pending_players:
            return

        target_index = self.game_state.current_player if starting_index is None else starting_index
        if target_index not in self.game_state.pending_players:
            total_players = len(self.game_state.players)
            for offset in range(total_players):
                candidate = (target_index + offset) % total_players
                if candidate in self.game_state.pending_players:
                    self.game_state.current_player = candidate
                    break
        else:
            self.game_state.current_player = target_index

    def _remove_inactive_from_pending(self):
        """Remove players who can no longer act from the pending set"""
        inactive = {
            idx for idx in list(self.game_state.pending_players)
            if idx >= len(self.game_state.players)
            or self.game_state.players[idx].is_folded
            or self.game_state.players[idx].is_all_in
            or self.game_state.players[idx].chips <= 0
        }
        self.game_state.pending_players -= inactive
    
    def start_gui(self):
        """Start the GUI"""
        try:
            import tkinter as tk
            from poker_gui import PokerGUI
            self.gui = PokerGUI(self)
            self.gui.run()
        except ImportError as e:
            print(f"GUI not available: {e}")
            print("Please install tkinter or run without GUI")
            return False

if __name__ == "__main__":
    game = GameManager()
    game.start_gui()
