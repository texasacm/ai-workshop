import os
import sys
import importlib.util
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import random
from enum import Enum

from poker_agents.agent_base import PokerAgentBase

class Suit(Enum):
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"

VALUE_NAMES = {
    14: "Ace",
    13: "King",
    12: "Queen",
    11: "Jack",
    10: "Ten",
    9: "Nine",
    8: "Eight",
    7: "Seven",
    6: "Six",
    5: "Five",
    4: "Four",
    3: "Three",
    2: "Two",
}

PLURAL_VALUE_NAMES = {
    14: "Aces",
    13: "Kings",
    12: "Queens",
    11: "Jacks",
    10: "Tens",
    9: "Nines",
    8: "Eights",
    7: "Sevens",
    6: "Sixes",
    5: "Fives",
    4: "Fours",
    3: "Threes",
    2: "Twos",
}

HAND_RANK_LABELS = {
    10: "Royal Flush",
    9: "Straight Flush",
    8: "Four of a Kind",
    7: "Full House",
    6: "Flush",
    5: "Straight",
    4: "Three of a Kind",
    3: "Two Pair",
    2: "One Pair",
    1: "High Card",
    0: "No Hand",
}

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
    def __init__(self, name: str, chips: int = 100, agent=None):
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
        self.last_action_display = None
        self.best_hand_rank = 0
        self.best_hand_name = None
        self.pending_invalid_reason = None
        self.is_eliminated = False
    
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
        self.last_action = None
        self.last_action_display = None
        self.best_hand_rank = 0
        self.best_hand_name = None
        self.pending_invalid_reason = None
        # do not reset is_eliminated here; elimination persists across hands

class GameState:
    def __init__(self):
        self.players = []
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.dealer_position = -1
        self.current_player = 0
        self.game_phase = "preflop"  # preflop, flop, turn, river, showdown
        self.deck = []
        self.winner = None
        self.pending_players = set()
        self.hand_count = 0
        
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
    def __init__(
        self,
        move_interval: float = 1.0,
        starting_chips: int = PokerAgentBase.STARTING_CHIPS,
        max_hand_limit: Optional[int] = None,
    ):
        """Initialize the game engine and eagerly load any available agents."""
        PokerAgentBase.STARTING_CHIPS = starting_chips
        self.game_state = GameState()
        self.gui = None
        self.move_interval = move_interval
        self.last_action_note = None
        self.pending_new_hand = False
        self.game_over = False
        self.starting_chips = starting_chips
        self.max_hand_limit = max_hand_limit
        self.load_agents()
    
    def load_agents(self):
        """Load poker agents from the poker_agents folder"""
        agents_folder = "poker_agents"
        if not os.path.exists(agents_folder):
            print(f"Warning: {agents_folder} folder not found")
            return

        agent_files = [
            f for f in os.listdir(agents_folder)
            if f.endswith('.py') and f not in ('agent_base.py', '__init__.py', 'agent_template.py')
        ]
        agent_files.sort()
        
        for i, agent_file in enumerate(agent_files):
            default_name = f"Agent {i+1}"
            try:
                spec = importlib.util.spec_from_file_location(
                    f"agent_{i}", 
                    os.path.join(agents_folder, agent_file)
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Try to instantiate the agent
                player = None
                if hasattr(module, 'PokerAgent'):
                    agent_cls = module.PokerAgent
                    agent = self._instantiate_agent(agent_cls, default_name)
                    if isinstance(agent, PokerAgentBase) and callable(getattr(agent, 'make_decision', None)):
                        agent.name = agent.name or default_name
                        agent.chips = self.starting_chips
                        player = Player(agent.name, self.starting_chips, agent)
                if player is None:
                    raise ValueError("Invalid PokerAgent implementation")
                player.position = i
                self.game_state.players.append(player)
                    
            except Exception as e:
                print(f"Error loading {agent_file}: {e}")
                # Create a default player on error
                player = Player(default_name, self.starting_chips)
                player.position = i
                self.game_state.players.append(player)

    def _instantiate_agent(self, agent_cls, fallback_name: str):
        """Instantiate an agent, allowing optional name injection."""
        try:
            return agent_cls()
        except TypeError:
            # Try again allowing name to be passed explicitly
            return agent_cls(name=fallback_name)

    def start_new_hand(self):
        """Start a new poker hand"""
        if self.game_over:
            return
        if (
            self.max_hand_limit is not None
            and self.game_state.hand_count >= self.max_hand_limit
        ):
            self._end_game_due_to_limit()
            return

        self.game_state.hand_count += 1
        self.game_state.reset_deck()
        self.game_state.community_cards = []
        self.game_state.pot = 0
        self.game_state.current_bet = 0
        self.game_state.winner = None
        self.pending_new_hand = False
        
        # Reset only active players (those with chips)
        for player in self.game_state.players:
            if player.is_eliminated:
                player.is_folded = True
                player.hole_cards = []
                player.last_action = "eliminated"
                player.last_action_display = "Eliminated"
                player.best_hand_rank = 0
                player.best_hand_name = None
                continue
            if player.chips > 0:  # Only reset players who are still in the game
                player.reset_for_new_hand()
            else:
                player.is_folded = True
                player.hole_cards = []
                player.best_hand_rank = 0
                player.best_hand_name = None
                player.pending_invalid_reason = None
        
        # Deal hole cards only to active players
        for _ in range(2):
            for player in self.game_state.players:
                if player.chips > 0 and not player.is_folded:
                    card = self.game_state.deal_card()
                    if card:
                        player.add_card(card)
        
        self.game_state.game_phase = "preflop"
        
        # Find first active player for current player
        first_player = self._pick_first_player_for_hand()
        self.game_state.current_player = first_player

        self._reset_pending_players(self.game_state.current_player)

        hand_msg = f"=== NEW HAND #{self.game_state.hand_count} DEALT ==="
        if self.gui:
            self.gui.log_message(hand_msg, color="info")
        else:
            self.last_action_note = hand_msg
        
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
            self.determine_winner()
        
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
        """Process a player's action; invalid attempts trigger an automatic fold."""
        if player_index >= len(self.game_state.players):
            return False
        
        player = self.game_state.players[player_index]
        if player.is_folded or player.is_all_in:
            self.game_state.pending_players.discard(player_index)
            return False

        success = False
        previous_bet = self.game_state.current_bet
        note_from_agent = player.pending_invalid_reason
        player.pending_invalid_reason = None
        self.last_action_note = None
        action_display = None
        
        if action == "fold":
            player.fold()
            success = True
            if note_from_agent:
                self.last_action_note = f"{note_from_agent} Automatic fold applied."
            action_display = "Fold"
        elif action == "call":
            call_amount = max(0, self.game_state.current_bet - player.current_bet)
            if call_amount == 0:
                success = True
                action_display = "Check"
            else:
                if call_amount > player.chips:
                    return self._auto_fold(
                        player_index,
                        f"attempted to call ${call_amount} with only ${player.chips}",
                    )
                if call_amount <= 0:
                    return self._auto_fold(player_index, "cannot call without chips")
                if player.bet(call_amount):
                    self.game_state.pot += call_amount
                    success = True
                    action_display = f"Call ${call_amount}"
        elif action == "raise":
            if amount is None:
                return self._auto_fold(player_index, "raise amount missing")
            if amount <= 0:
                return self._auto_fold(player_index, "raise amount must be positive")
            call_amount = max(0, self.game_state.current_bet - player.current_bet)
            total_commit = call_amount + amount
            if total_commit > player.chips:
                return self._auto_fold(
                    player_index,
                    f"raise requires ${total_commit} but only ${player.chips} available",
                )
            if total_commit <= 0:
                return self._auto_fold(player_index, "raise must increase the bet")
            if player.bet(total_commit):
                self.game_state.pot += total_commit
                success = True
                action_display = f"Raise to ${player.current_bet}"
        elif action == "check":
            if self.game_state.current_bet == player.current_bet:
                success = True
                action_display = "Check"
            else:
                return self._auto_fold(player_index, "cannot check while facing a bet")
        else:
            return self._auto_fold(player_index, f"unknown action '{action}'")

        if not success:
            return self._auto_fold(player_index, f"failed to execute {action}")

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
        
        player.last_action = action
        if player.is_all_in and action_display:
            action_display += " (All-In)"
        player.last_action_display = action_display or action.title()
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
        # Frequency distribution simplifies identifying pairs, trips, etc.
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
        # Reset previously stored hand summaries before evaluating fresh results
        for player in self.game_state.players:
            player.best_hand_rank = 0
            player.best_hand_name = None

        active_players = [p for p in self.game_state.players if not p.is_folded]
        
        if len(active_players) == 1:
            active_players[0].best_hand_rank = 1
            active_players[0].best_hand_name = "Last Player Standing"
            return active_players
        
        # Evaluate each player's best hand
        player_hands = []
        for player in active_players:
            all_cards = player.hole_cards + self.game_state.community_cards
            hand_rank, kickers = self.evaluate_hand(all_cards)
            player.best_hand_rank = hand_rank
            player.best_hand_name = self._hand_rank_to_name(hand_rank, kickers)
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

        # Eliminate players who failed to rebuild their stack and did not win the pot
        for player in self.game_state.players:
            if player in winners and player.chips > 0:
                player.is_eliminated = False
            elif player.chips == 0 and player not in winners:
                player.is_eliminated = True
                player.is_folded = True
                player.last_action_display = "Eliminated"

        # Victory check: one player holds every chip
        total_chips = sum(p.chips for p in self.game_state.players)
        champions = [p for p in self.game_state.players if p.chips == total_chips and total_chips > 0]
        if champions and all(p.is_eliminated or p in champions for p in self.game_state.players):
            winner = champions[0]
            self.game_over = True
            victory_msg = f"🎉 {winner.name} wins the tournament! 🎉"
            self.last_action_note = victory_msg
            if self.gui:
                self.gui.log_message(victory_msg, color="info")
    
    def get_random_action(self, player: Player) -> Tuple[str, int]:
        """Get a random action for a player"""
        actions = ["fold", "call", "check", "raise"]
        weights = [0.1, 0.3, 0.3, 0.3]  # Favor call/check/raise over fold
        
        action = random.choices(actions, weights=weights)[0]
        amount = 0
        call_amount = max(0, self.game_state.current_bet - player.current_bet)

        if action == "raise":
            max_additional = player.chips - call_amount
            if max_additional <= 0:
                if call_amount > 0 and player.chips > 0:
                    return "call", min(call_amount, player.chips)
                return "check", 0

            raise_cap = min(25, max_additional)
            if raise_cap < 1:
                if call_amount > 0 and player.chips > 0:
                    return "call", min(call_amount, player.chips)
                return "check", 0

            min_raise = max(1, min(5, raise_cap))
            amount = random.randint(min_raise, raise_cap) if raise_cap >= min_raise else raise_cap
            amount = max(1, amount)

            if call_amount + amount > player.chips:
                amount = player.chips - call_amount
                if amount <= 0:
                    if call_amount > 0 and player.chips > 0:
                        return "call", min(call_amount, player.chips)
                    return "check", 0

            return "raise", amount

        if action == "call":
            if call_amount == 0:
                return "check", 0
            return "call", min(call_amount, player.chips)
        
        if action == "check":
            return "check", 0
        
        return "fold", 0
    
    def play_autonomous_round(self):
        """Play one round of autonomous poker"""
        if self.game_over:
            return False

        # Deal a new hand if the previous showdown requested one
        if self.pending_new_hand:
            self.start_new_hand()
            if self.game_over:
                return False
            if self.gui:
                self.gui.update_display()
            return True

        # Check if only one non-eliminated player remains with chips
        active_players = [p for p in self.game_state.players if not p.is_eliminated]
        if len(active_players) <= 1:
            if len(active_players) == 1:
                winner = active_players[0]
                self.game_over = True
                msg = f"🎉 GAME OVER! {winner.name} WINS THE TOURNAMENT! 🎉"
                self.last_action_note = msg
                if self.gui:
                    self.gui.log_message(msg, color="info")
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
                    self.gui.update_display()
                    self.gui.log_message(f"Winners: {', '.join(winner_names)} win ${pot_amount}")
                else:
                    self.last_action_note = f"Winners: {', '.join(winner_names)} win ${pot_amount}"
                self.pending_new_hand = True
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
        agent = player.agent
        if agent and hasattr(agent, 'make_decision'):
            try:
                game_state = self._build_agent_game_state(player)
                prepared = False
                if isinstance(agent, PokerAgentBase):
                    agent._prepare_turn(game_state)
                    prepared = True
                decision = agent.make_decision(game_state)
                action, amount = self._normalize_agent_action(decision)
                if action is None or not self._is_valid_agent_action(player, action, amount):
                    player.pending_invalid_reason = (
                        f"{player.name}'s agent attempted an invalid move ({decision})."
                    )
                    if isinstance(agent, PokerAgentBase):
                        agent.debug(
                            f"Invalid decision {decision} with call_required={game_state['call_required']} "
                            f"and stack={player.chips}"
                        )
                    return "fold", 0
                if action == "all-in":
                    call_required = game_state['call_required']
                    available = player.chips
                    if available <= 0:
                        return "fold", 0
                    if call_required > available:
                        if isinstance(agent, PokerAgentBase):
                            agent.debug(
                                f"Invalid all-in: needs ${call_required} to call but only has ${available}"
                            )
                        return "fold", 0
                    raise_amount = available - call_required
                    if raise_amount <= 0:
                        return "call", available
                    return "raise", raise_amount
                return action, amount
            except Exception as exc:
                if isinstance(agent, PokerAgentBase):
                    agent.debug(f"Error during decision: {exc}")
                return "fold", 0
            finally:
                if isinstance(agent, PokerAgentBase):
                    agent._finish_turn()
        
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

            if (candidate_player.is_folded or candidate_player.is_all_in or
                    candidate_player.chips <= 0 or candidate_player.is_eliminated):
                continue
            if self.game_state.pending_players and candidate not in self.game_state.pending_players:
                continue

            self.game_state.current_player = candidate
            return

        # Fallback to original player if no valid candidate found
        self.game_state.current_player = start_index

    def _pick_first_player_for_hand(self) -> int:
        """Rotate the first-to-act position, skipping eliminated or broke players."""
        players = self.game_state.players
        if not players:
            return 0
        total_players = len(players)
        start = (self.game_state.dealer_position + 1) % total_players
        for offset in range(total_players):
            candidate = (start + offset) % total_players
            candidate_player = players[candidate]
            if candidate_player.chips > 0 and not candidate_player.is_eliminated:
                self.game_state.dealer_position = candidate
                return candidate
        return 0

    def _end_game_due_to_limit(self):
        """Declare a winner when the configured hand limit is reached."""
        if self.game_over:
            return

        players = self.game_state.players
        winners = []
        max_chips = 0
        if players:
            max_chips = max(p.chips for p in players)
            winners = [p for p in players if p.chips == max_chips]

        self.game_state.winner = winners if len(winners) != 1 else winners[0]
        self.game_over = True
        self.pending_new_hand = False
        self.game_state.pending_players.clear()

        if not winners:
            message = "Hand limit reached. No winners could be determined."
        elif len(winners) == 1:
            message = (
                f"Hand limit reached. {winners[0].name} wins with ${max_chips} in chips."
            )
        else:
            names = ", ".join(p.name for p in winners)
            message = (
                f"Hand limit reached. {names} tie for the lead with ${max_chips} each."
            )

        self.last_action_note = message
        if self.gui:
            self.gui.log_message(message, color="info")
            self.gui.show_status_message(message, error=False)
            self.gui.update_display()

    def _players_who_can_act(self):
        """Return indices of players who can take an action"""
        return [
            idx for idx, player in enumerate(self.game_state.players)
            if (not player.is_folded and not player.is_all_in and
                player.chips > 0 and not player.is_eliminated)
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
    
    def _auto_fold(self, player_index: int, reason: str) -> bool:
        """Force a player to fold after an invalid move and record a user-facing message."""
        if player_index >= len(self.game_state.players):
            return False
        player = self.game_state.players[player_index]
        if not player.is_folded:
            player.fold()
            player.last_action = "fold"
        player.last_action_display = "Invalid -> Fold"
        player.pending_invalid_reason = None
        if isinstance(player.agent, PokerAgentBase):
            player.agent.debug(f"Forcing fold: {reason}")
        self.game_state.pending_players.discard(player_index)
        self.last_action_note = f"{player.name}: invalid action - {reason}. Automatic fold applied."
        return True

    def pop_last_action_note(self) -> Optional[str]:
        """Return and clear the latest action note (e.g., invalid move warnings)."""
        note = self.last_action_note
        self.last_action_note = None
        return note

    def _hand_rank_to_name(self, hand_rank: int, kickers: List[int]) -> str:
        """Translate a numeric hand rank and kickers into a human-readable label."""
        label = HAND_RANK_LABELS.get(hand_rank, "Unknown Hand")
        if hand_rank == 10:  # Royal Flush
            return label
        if hand_rank == 9:  # Straight Flush
            return f"{label} ({self._value_to_name(kickers[0])} high)"
        if hand_rank == 8:  # Four of a Kind
            return f"Four of {self._value_to_plural_name(kickers[0])}"
        if hand_rank == 7:  # Full House
            return (
                f"Full House ({self._value_to_plural_name(kickers[0])} over "
                f"{self._value_to_plural_name(kickers[1])})"
            )
        if hand_rank == 6:  # Flush
            return f"Flush ({self._value_to_name(kickers[0])} high)"
        if hand_rank == 5:  # Straight
            return f"Straight to {self._value_to_name(kickers[0])}"
        if hand_rank == 4:  # Three of a Kind
            return f"Three of {self._value_to_plural_name(kickers[0])}"
        if hand_rank == 3:  # Two Pair
            high_pair, low_pair = kickers[:2]
            return (
                f"Two Pair ({self._value_to_plural_name(high_pair)} and "
                f"{self._value_to_plural_name(low_pair)})"
            )
        if hand_rank == 2:  # One Pair
            return f"Pair of {self._value_to_plural_name(kickers[0])}"
        if hand_rank == 1:  # High Card
            return f"High Card {self._value_to_name(kickers[0])}"
        return label

    def _value_to_name(self, value: int) -> str:
        """Return the singular card rank name for a numeric value."""
        return VALUE_NAMES.get(value, str(value))

    def _value_to_plural_name(self, value: int) -> str:
        """Return the pluralised card rank name for a numeric value."""
        return PLURAL_VALUE_NAMES.get(value, f"{self._value_to_name(value)}s")

    def _build_agent_game_state(self, player: Player) -> Dict[str, Any]:
        """Create a restricted game state view for agents."""
        player_index = self.game_state.players.index(player)
        total_players = len(self.game_state.players)
        previous_player = None
        if total_players > 1:
            previous_player = self.game_state.players[(player_index - 1) % total_players]
        # Amount this player must contribute to call the current bet
        call_required = max(0, self.game_state.current_bet - player.current_bet)

        return {
            'self': {
                'name': player.name,
                'chips': player.chips,
                'hole_cards': list(player.hole_cards),
                'current_bet': player.current_bet,
                'total_bet': player.total_bet,
                'is_all_in': player.is_all_in,
            },
            'community_cards': list(self.game_state.community_cards),
            'pot': self.game_state.pot,
            'current_bet': self.game_state.current_bet,
            'call_required': call_required,
            'game_phase': self.game_state.game_phase,
            'other_player_moves': [
                {
                    'name': other.name,
                    'last_action': other.last_action,
                }
                for other in self.game_state.players
                if other is not player
            ],
            'previous_player_action': (
                {
                    'name': previous_player.name,
                    'last_action': previous_player.last_action,
                }
                if previous_player and previous_player is not player
                else None
            ),
        }

    def _normalize_agent_action(self, decision) -> Tuple[Optional[str], Optional[int]]:
        """Normalize an agent's decision into (action, amount)."""
        action = None
        amount = 0

        if isinstance(decision, tuple):
            if not decision:
                return None, None
            action = decision[0]
            amount = decision[1] if len(decision) > 1 else 0
        else:
            action = decision
            amount = 0

        if not isinstance(action, str):
            return None, None

        action = action.strip().lower()

        if action in {"fold", "check"}:
            return action, 0

        if action in {"all-in", "all in", "allin", "shove"}:
            return "all-in", None

        try:
            amount_value = int(amount)
        except (TypeError, ValueError):
            return action, None

        if amount_value < 0:
            return action, None

        return action, amount_value

    def _is_valid_agent_action(self, player: Player, action: str, amount: Optional[int]) -> bool:
        """Validate an agent-provided action."""
        allowed_actions = {"fold", "check", "call", "raise", "all-in"}
        if action not in allowed_actions:
            return False

        call_required = max(0, self.game_state.current_bet - player.current_bet)
        available = player.chips

        if action == "fold":
            return True

        if action == "check":
            return call_required == 0 and (amount in (0, None))

        if action == "all-in":
            return available > 0

        if action == "call":
            if call_required == 0:
                return amount in (0, None)
            if available <= 0 or amount is None:
                return False
            if call_required > available:
                return False
            return amount == call_required

        if action == "raise":
            if amount is None or amount <= 0:
                return False
            if available <= call_required:
                return False
            total_commit = call_required + amount
            if total_commit > available:
                return False
            return True

        return False
    
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
