"""
CFR-Inspired Poker Agent with Hand Bucketing

This agent uses:
- 8 preflop hand strength buckets
- 5 postflop equity buckets (Monte Carlo simulation)
- Position-aware strategy (early/middle/late)
- SPR-based adjustments
- CFR-inspired pot-based bet sizing
- Equity-based bluffing
"""
import random
from typing import List, Tuple, Dict, Any
from poker_agents.agent_base import PokerAgentBase
from itertools import combinations


class PokerAgent(PokerAgentBase):
    DEFAULT_NAME = "CFR Agent"

    # Preflop hand strength buckets (8 buckets)
    PREFLOP_BUCKETS = {
        # Bucket 0: Premium pairs and AK
        0: ['AA', 'KK', 'QQ', 'AKs', 'AKo'],
        # Bucket 1: Strong pairs and Broadway
        1: ['JJ', 'TT', 'AQs', 'AQo', 'AJs', 'AKo'],
        # Bucket 2: Medium pairs and strong aces
        2: ['99', '88', '77', 'ATs', 'AJo', 'KQs'],
        # Bucket 3: Small pairs and suited connectors
        3: ['66', '55', '44', 'KQo', 'ATo', 'KJs', 'QJs', 'JTs'],
        # Bucket 4: Suited aces and connectors
        4: ['33', '22', 'A9s', 'A8s', 'A7s', 'KTs', 'QTs', 'J9s', 'T9s', '98s'],
        # Bucket 5: Marginal hands
        5: ['A6s', 'A5s', 'A4s', 'A3s', 'A2s', 'K9s', 'Q9s', 'J8s', 'T8s', '97s', '87s', '76s'],
        # Bucket 6: Weak offsuit broadways
        6: ['KJo', 'QJo', 'JTo', 'KTo', 'QTo'],
        # Bucket 7: Trash
        7: []  # Everything else
    }

    def __init__(self, name=None):
        super().__init__(name or self.DEFAULT_NAME)
        # Increase Monte Carlo iterations slightly to reduce sampling variance
        # while keeping runtime reasonable for tests.
        self.monte_carlo_iterations = 500  # Lower variance than 200

    def make_decision(self, game_state):
        """Main decision-making logic"""
        phase = self.state['game_phase']
        
        if phase == 'preflop':
            return self._preflop_decision()
        else:
            return self._postflop_decision()

    # ==================== PREFLOP LOGIC ====================
    
    def _preflop_decision(self) -> Tuple[str, int]:
        """Preflop decision based on hand bucketing, position, and SPR"""
        bucket = self._get_preflop_bucket()
        position = self._get_position()
        spr = self._get_spr()
        num_players = self._get_active_player_count()
        call_required = self.call_required
        stack = self.stack
        pot = self.state['pot']
        
        # Adjust bucket threshold based on position and player count
        position_adjustment = {'early': 0, 'middle': 1, 'late': 2}
        effective_bucket = bucket - position_adjustment[position]
        
        # Tighter with more players
        if num_players >= 6:
            effective_bucket -= 1
        elif num_players <= 3:
            effective_bucket += 1
            
        # Decision matrix based on effective bucket
        if effective_bucket <= 0:  # Premium hands
            return self._premium_preflop_action(call_required, stack, pot, spr)
        elif effective_bucket <= 2:  # Strong hands
            return self._strong_preflop_action(call_required, stack, pot, spr)
        elif effective_bucket <= 4:  # Medium hands
            return self._medium_preflop_action(call_required, stack, pot, spr, position)
        elif effective_bucket <= 6:  # Marginal hands
            return self._marginal_preflop_action(call_required, stack, pot, position)
        else:  # Trash
            return self._trash_preflop_action(call_required, stack, pot)

    def _premium_preflop_action(self, call_required, stack, pot, spr) -> Tuple[str, int]:
        """Action for premium hands (AA, KK, QQ, AK)"""
        if call_required == 0:
            # Raise 3x pot or 2/3 pot
            raise_size = min(int(pot * 0.66), stack)
            if raise_size > 0:
                return self.raise_by(raise_size)
            return self.check()
        
        # Facing a bet
        if call_required >= stack * 0.5:
            # Large bet - go all-in with premium
            return self.all_in()
        
        # 3-bet with premium hands
        three_bet_size = min(call_required * 3, stack - call_required)
        if three_bet_size > 0:
            return self.raise_by(three_bet_size)
        return self.call()

    def _strong_preflop_action(self, call_required, stack, pot, spr) -> Tuple[str, int]:
        """Action for strong hands (JJ, TT, AQ, AJ)"""
        if call_required == 0:
            # Raise 2/3 pot
            raise_size = min(int(pot * 0.66), stack)
            if raise_size > 0:
                return self.raise_by(raise_size)
            return self.check()
        
        # Facing a bet
        pot_odds = call_required / (pot + call_required) if (pot + call_required) > 0 else 1
        
        if call_required >= stack * 0.7:
            # Very large bet - deterministically choose based on SPR
            if spr < 5:  # committed-ish -> shove
                return self.all_in()
            # otherwise, fold to an extremely large bet
            return self.fold()
        
        if call_required >= stack * 0.3:
            # Large bet - 3-bet when SPR is favorable, otherwise call
            if spr > 3:
                three_bet = min(call_required * 2, stack - call_required)
                if three_bet > 0:
                    return self.raise_by(three_bet)
            return self.call()
        
        # Small bet - raise
        raise_size = min(call_required * 2, stack - call_required)
        # Prefer raising when it's a meaningful raise (deterministic)
        if raise_size > 0 and pot > 0:
            return self.raise_by(raise_size)
        return self.call()

    def _medium_preflop_action(self, call_required, stack, pot, spr, position) -> Tuple[str, int]:
        """Action for medium hands (99-77, suited broadways)"""
        if call_required == 0:
            # Raise deterministically from late and middle positions (steal/pressure)
            if position in ('late', 'middle'):
                raise_size = min(int(pot * 0.5), stack)
                if raise_size > 0:
                    return self.raise_by(raise_size)
            return self.check()
        
        # Facing a bet
        pot_odds = call_required / (pot + call_required) if (pot + call_required) > 0 else 1
        
        if call_required >= stack * 0.5:
            # Large bet - fold most of the time
            if spr < 3:  # Very committed
                return self.call() if call_required <= stack else self.fold()
            return self.fold()
        
        if call_required >= stack * 0.2:
            # Medium bet - call from late or when pot odds are attractive,
            # otherwise fold deterministically to avoid variance.
            if position == 'late' or pot_odds < 0.25:
                return self.call() if call_required <= stack else self.fold()
            return self.fold()
        
        # Small bet - call
        return self.call() if call_required <= stack else self.fold()

    def _marginal_preflop_action(self, call_required, stack, pot, position) -> Tuple[str, int]:
        """Action for marginal hands (small pairs, suited aces)"""
        if call_required == 0:
            # Raise deterministically from late position when pot is small (steal)
            if position == 'late' and pot < stack * 0.1:
                raise_size = min(int(pot * 0.5), stack)
                if raise_size > 0:
                    return self.raise_by(raise_size)
            return self.check()
        
        # Facing a bet
        pot_odds = call_required / (pot + call_required) if (pot + call_required) > 0 else 1
        
        if call_required >= stack * 0.15:
            # Any significant bet - fold
            return self.fold()
        
        # Very cheap to call - call for implied odds with small pairs/suited aces
        if pot_odds < 0.1 and position == 'late':
            return self.call() if call_required <= stack else self.fold()
        
        return self.fold()

    def _trash_preflop_action(self, call_required, stack, pot) -> Tuple[str, int]:
        """Action for trash hands"""
        if call_required == 0:
            return self.check()
        
        # Fold to any bet
        return self.fold()

    # ==================== POSTFLOP LOGIC ====================
    
    def _postflop_decision(self) -> Tuple[str, int]:
        """Postflop decision based on equity calculation and board texture"""
        equity = self._calculate_equity_monte_carlo()
        bucket = self._get_postflop_bucket(equity)
        position = self._get_position()
        spr = self._get_spr()
        call_required = self.call_required
        stack = self.stack
        pot = self.state['pot']
        
        # Get draw potential for bluffing decisions
        has_draw = self._has_draw()
        
        # Decision based on equity bucket
        if bucket == 0:  # Very strong (equity > 0.75)
            return self._very_strong_postflop(call_required, stack, pot, spr)
        elif bucket == 1:  # Strong (0.55 - 0.75)
            return self._strong_postflop(call_required, stack, pot, spr, position)
        elif bucket == 2:  # Medium (0.40 - 0.55)
            return self._medium_postflop(call_required, stack, pot, spr, position, has_draw)
        elif bucket == 3:  # Weak (0.25 - 0.40)
            return self._weak_postflop(call_required, stack, pot, position, has_draw, equity)
        else:  # Very weak (< 0.25)
            return self._very_weak_postflop(call_required, stack, pot, position, has_draw, equity)

    def _very_strong_postflop(self, call_required, stack, pot, spr) -> Tuple[str, int]:
        """Action with very strong hands (nuts, near-nuts)"""
        if call_required == 0:
            # Bet for value - pick a deterministic strong sizing (pot or 2/3 pot)
            bet_size = min(pot if pot > 0 else int(pot * 0.66), stack)
            if bet_size > 0:
                return self.raise_by(bet_size)
            return self.check()
        
        # Facing a bet - always raise or call
        if call_required >= stack * 0.8:
            return self.all_in()
        
        # Raise for value
        # Deterministically raise for value when reasonable
        raise_sizes = [call_required, call_required * 2]
        raise_size = min(max(raise_sizes), stack - call_required) if raise_sizes else 0
        if raise_size > 0:
            return self.raise_by(raise_size)
        
        return self.call() if call_required <= stack else self.all_in()

    def _strong_postflop(self, call_required, stack, pot, spr, position) -> Tuple[str, int]:
        """Action with strong hands"""
        if call_required == 0:
            # Bet for value - 2/3 pot
            bet_size = min(int(pot * 0.66), stack)
            if bet_size > 0:
                return self.raise_by(bet_size)
            return self.check()
        
        # Facing a bet
        pot_odds = call_required / (pot + call_required) if (pot + call_required) > 0 else 1
        
        if call_required >= stack * 0.7:
            # Large bet - call or shove based on SPR deterministically
            if spr < 3:
                return self.all_in()
            return self.call() if call_required <= stack else self.fold()
        
        # Medium bet - raise sometimes, call sometimes
        # Raise for protection/value when pot odds are favorable (deterministic)
        pot_odds = call_required / (pot + call_required) if (pot + call_required) > 0 else 1
        if pot_odds < 0.25:
            raise_size = min(call_required * 2, stack - call_required)
            if raise_size > 0:
                return self.raise_by(raise_size)
        
        return self.call() if call_required <= stack else self.fold()

    def _medium_postflop(self, call_required, stack, pot, spr, position, has_draw) -> Tuple[str, int]:
        """Action with medium strength hands"""
        if call_required == 0:
            # Deterministic protection bet from late position
            bet_size = min(int(pot * 0.5), stack)
            if bet_size > 0 and position == 'late':
                return self.raise_by(bet_size)
            return self.check()
        
        # Facing a bet
        pot_odds = call_required / (pot + call_required) if (pot + call_required) > 0 else 1
        
        if call_required >= stack * 0.5:
            # Large bet - fold usually
            if spr < 2:
                return self.call() if call_required <= stack else self.fold()
            return self.fold()
        
        # Getting good odds - call
        if pot_odds < 0.33:
            return self.call() if call_required <= stack else self.fold()
        
        # Marginal odds - call from late, fold otherwise
        if position == 'late' or position == 'middle':
            return self.call() if call_required <= stack else self.fold()
        
        return self.fold()

    def _weak_postflop(self, call_required, stack, pot, position, has_draw, equity) -> Tuple[str, int]:
        """Action with weak hands (might have draws)"""
        if call_required == 0:
            # Check or bluff based on position and draws
            if has_draw and position == 'late' and random.random() < equity:
                # Semi-bluff with draws
                bet_size = min(int(pot * 0.33), stack)
                if bet_size > 0:
                    return self.raise_by(bet_size)
            return self.check()
        
        # Facing a bet
        pot_odds = call_required / (pot + call_required) if (pot + call_required) > 0 else 1
        
        if has_draw:
            # With a draw, call if getting right odds
            # Roughly need 4:1 for flush draw, 5:1 for straight draw
            if pot_odds < 0.20:  # Better than 5:1
                return self.call() if call_required <= stack else self.fold()
        
        # No draw or bad odds - fold
        if call_required >= stack * 0.15:
            return self.fold()
        
        # Very cheap - call sometimes
        if pot_odds < 0.1 and random.random() < 0.3:
            return self.call() if call_required <= stack else self.fold()
        
        return self.fold()

    def _very_weak_postflop(self, call_required, stack, pot, position, has_draw, equity) -> Tuple[str, int]:
        """Action with very weak hands"""
        if call_required == 0:
            # Bluff occasionally from late position with draws
            if has_draw and position == 'late' and random.random() < equity * 0.5:
                bet_size = min(int(pot * 0.33), stack)
                if bet_size > 0:
                    return self.raise_by(bet_size)
            return self.check()
        
        # Facing a bet - fold unless getting amazing odds with a draw
        if has_draw:
            pot_odds = call_required / (pot + call_required) if (pot + call_required) > 0 else 1
            if pot_odds < 0.15 and call_required < stack * 0.1:
                return self.call() if call_required <= stack else self.fold()
        
        return self.fold()

    # ==================== HELPER FUNCTIONS ====================
    
    def _get_preflop_bucket(self) -> int:
        """Determine preflop hand bucket (0-7)"""
        hole_cards = self.hero['hole_cards']
        if len(hole_cards) != 2:
            return 7  # Trash

        card1, card2 = hole_cards
        rank1, rank2 = card1.rank, card2.rank
        suit1, suit2 = card1.suit, card2.suit
        
        # Normalize rank strings to match bucket notation ('T' used for Ten in PREFLOP_BUCKETS)
        # GameManager uses '10' for Ten; convert to 'T' here so lookups succeed.
        if rank1 == '10':
            rank1 = 'T'
        if rank2 == '10':
            rank2 = 'T'

        # Convert ranks to numeric values for comparison
        val1 = card1.get_value()
        val2 = card2.get_value()
        
        # Order by value
        if val1 < val2:
            val1, val2 = val2, val1
            rank1, rank2 = rank2, rank1
        
        is_suited = suit1 == suit2
        is_pair = val1 == val2
        
        # Create hand string
        if is_pair:
            hand_str = f"{rank1}{rank2}"
        else:
            hand_str = f"{rank1}{rank2}{'s' if is_suited else 'o'}"
        
        # Check each bucket
        for bucket_num, hands in self.PREFLOP_BUCKETS.items():
            if hand_str in hands:
                return bucket_num
        
        # Special handling for pairs
        if is_pair:
            if val1 >= 10:
                return 1  # TT+
            elif val1 >= 7:
                return 2  # 77-99
            elif val1 >= 4:
                return 3  # 44-66
            else:
                return 4  # 22-33
        
        # High card hands
        if val1 == 14:  # Ace-x
            if is_suited:
                return 5  # Suited ace
            if val2 >= 10:
                return 2  # ATo+
            return 6  # Weak ace
        
        # Suited connectors
        if is_suited and abs(val1 - val2) <= 2:
            return 5
        
        # Offsuit broadways
        if val1 >= 10 and val2 >= 10:
            return 6
        
        return 7  # Trash

    def _get_postflop_bucket(self, equity: float) -> int:
        """Convert equity to bucket (0-4)"""
        if equity >= 0.75:
            return 0  # Very strong
        elif equity >= 0.55:
            return 1  # Strong
        elif equity >= 0.40:
            return 2  # Medium
        elif equity >= 0.25:
            return 3  # Weak
        else:
            return 4  # Very weak

    def _calculate_equity_monte_carlo(self) -> float:
        """Calculate hand equity using Monte Carlo simulation"""
        hole_cards = self.hero['hole_cards']
        community_cards = self.state['community_cards']
        
        if not hole_cards:
            return 0.0
        
        # Simple hand strength if no community cards yet
        if not community_cards:
            return self._preflop_hand_strength()
        
        # Run Monte Carlo simulation
        wins = 0
        ties = 0
        
        for _ in range(self.monte_carlo_iterations):
            # Create a deck without known cards
            deck = self._create_deck_without(hole_cards + community_cards)
            random.shuffle(deck)
            
            # Deal remaining community cards
            remaining_community = len(community_cards)
            simulated_board = community_cards + deck[:5 - remaining_community]
            
            # Deal opponent cards
            opp_cards = deck[5 - remaining_community:7 - remaining_community]
            
            # Evaluate hands
            my_hand = hole_cards + simulated_board
            opp_hand = opp_cards + simulated_board
            
            my_rank = self._evaluate_hand_strength(my_hand)
            opp_rank = self._evaluate_hand_strength(opp_hand)
            
            if my_rank > opp_rank:
                wins += 1
            elif my_rank == opp_rank:
                ties += 0.5
        
        equity = (wins + ties) / self.monte_carlo_iterations
        return equity

    def _preflop_hand_strength(self) -> float:
        """Simple preflop hand strength estimation"""
        bucket = self._get_preflop_bucket()
        # Map buckets to approximate equity vs random hand
        equity_map = {
            0: 0.85,  # Premium
            1: 0.70,  # Strong
            2: 0.60,  # Medium
            3: 0.52,  # Small pairs/suited
            4: 0.48,  # Suited aces
            5: 0.45,  # Marginal
            6: 0.42,  # Weak
            7: 0.35,  # Trash
        }
        return equity_map.get(bucket, 0.35)

    def _create_deck_without(self, excluded_cards: List) -> List:
        """Create a deck excluding specific cards"""
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        from game_manager import Card, Suit
        suits = [Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS, Suit.SPADES]
        
        deck = []
        for rank in ranks:
            for suit in suits:
                card = Card(rank, suit)
                # Check if this card is excluded
                is_excluded = False
                for exc_card in excluded_cards:
                    if exc_card.rank == card.rank and exc_card.suit == card.suit:
                        is_excluded = True
                        break
                if not is_excluded:
                    deck.append(card)
        
        return deck

    def _evaluate_hand_strength(self, cards: List) -> Tuple[int, List[int]]:
        """Evaluate hand strength (simplified version of GameManager's evaluate_hand)"""
        if len(cards) < 5:
            values = sorted([card.get_value() for card in cards], reverse=True)
            return (1 if values else 0, values)
        
        # Get best 5-card combination
        best_hand = (0, [])
        
        for combo in combinations(cards, 5):
            hand_rank, kickers = self._evaluate_five_cards(list(combo))
            if hand_rank > best_hand[0] or (hand_rank == best_hand[0] and kickers > best_hand[1]):
                best_hand = (hand_rank, kickers)
        
        return best_hand

    def _evaluate_five_cards(self, cards: List) -> Tuple[int, List[int]]:
        """Evaluate a 5-card hand"""
        from collections import Counter
        
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
        
        # Royal flush or straight flush
        if is_flush and is_straight:
            if straight_high == 14 and sorted(values) == [10, 11, 12, 13, 14]:
                return (10, [14])
            return (9, [straight_high])
        
        # Four of a kind
        if counts[0] == 4:
            return (8, [ordered_vals[0]])
        
        # Full house
        if counts[0] == 3 and len(counts) > 1 and counts[1] == 2:
            return (7, [ordered_vals[0], ordered_vals[1]])
        
        # Flush
        if is_flush:
            return (6, sorted_values_desc)
        
        # Straight
        if is_straight:
            return (5, [straight_high])
        
        # Three of a kind
        if counts[0] == 3:
            return (4, [ordered_vals[0]])
        
        # Two pair
        if counts[0] == 2 and len(counts) > 1 and counts[1] == 2:
            return (3, [ordered_vals[0], ordered_vals[1]])
        
        # One pair
        if counts[0] == 2:
            return (2, [ordered_vals[0]])
        
        # High card
        return (1, sorted_values_desc)

    def _is_straight(self, values: List[int]) -> Tuple[bool, int]:
        """Check if values form a straight"""
        unique_values = sorted(set(values))
        if len(unique_values) != 5:
            return False, 0
        
        # Wheel straight (A-2-3-4-5)
        if unique_values == [2, 3, 4, 5, 14]:
            return True, 5
        
        # Regular straight
        for i in range(4):
            if unique_values[i + 1] - unique_values[i] != 1:
                return False, 0
        
        return True, unique_values[-1]

    def _has_draw(self) -> bool:
        """Check if we have a flush or straight draw"""
        hole_cards = self.hero['hole_cards']
        community_cards = self.state['community_cards']
        
        if not community_cards or len(community_cards) < 3:
            return False
        
        all_cards = hole_cards + community_cards
        
        # Check for flush draw (4 of same suit)
        from collections import Counter
        suit_counts = Counter(card.suit for card in all_cards)
        if max(suit_counts.values()) >= 4:
            return True
        
        # Check for straight draw (open-ended or gutshot)
        values = sorted([card.get_value() for card in all_cards])
        unique_values = sorted(set(values))
        
        # Check for 4-card straight possibilities
        if len(unique_values) >= 4:
            for i in range(len(unique_values) - 3):
                window = unique_values[i:i+4]
                if window[-1] - window[0] == 3:  # Open-ended
                    return True
                if window[-1] - window[0] == 4:  # Gutshot
                    return True
        
        # Check for wheel draw (A-2-3-4)
        if 14 in unique_values and 2 in unique_values:
            low_cards = [v for v in unique_values if v <= 5]
            if len(low_cards) >= 3:
                return True
        
        return False

    def _get_position(self) -> str:
        """Determine our position at the table"""
        num_players = len(self.state['other_player_moves']) + 1
        
        # Get our position relative to button
        # For simplicity, divide table into thirds
        if num_players <= 3:
            return 'late'
        elif num_players <= 6:
            # Small table
            return 'middle'
        else:
            # Full table - this is simplified, would need actual button position
            return 'middle'

    def _get_spr(self) -> float:
        """Calculate Stack-to-Pot Ratio"""
        pot = self.state['pot']
        stack = self.stack
        
        if pot == 0:
            return float('inf')
        
        return stack / pot

    def _get_active_player_count(self) -> int:
        """Count number of active (non-folded) players"""
        other_players = self.state['other_player_moves']
        active_count = 1  # Count ourselves
        
        for player in other_players:
            if player['last_action'] != 'fold':
                active_count += 1
        
        return active_count
