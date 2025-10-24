"""
Template poker agent.

Copy this file, rename it, and fill in the decision logic.
"""
from typing import Optional, Tuple

from poker_agents.agent_base import PokerAgentBase


class PokerAgent(PokerAgentBase):
    """
    Example agent implementation.

    Agents receive a restricted game_state dictionary with:
      - self: your visible state (chips, hole_cards, current_bet, total_bet, is_all_in)
      - community_cards: community cards that have been revealed
      - pot: current size of the shared pot
      - current_bet: table-wide bet you must match to stay in the hand
      - call_required: how many chips you must commit to call
      - game_phase: one of 'preflop', 'flop', 'turn', 'river', 'showdown'
      - other_player_moves: list of dicts with each opponent's name and last action
      - previous_player_action: the name/action of the player who acted immediately before you
    Agents must return either a string action ('fold', 'check', 'call', 'raise')
    or a tuple of (action, amount) for raises/calls.

    Convenience helpers available during make_decision:
      - self.state / self.hero for quick access to the cached game state
      - self.call_required / self.stack for numeric shortcuts
      - self.check(), self.call(), self.raise_by(amount), self.all_in()
        which emit properly formatted actions for the GameManager
    """

    DEFAULT_NAME = "PriscillaPokerAgent"

    def __init__(self, name: Optional[str] = None):
        super().__init__(name or self.DEFAULT_NAME)


    def _board_texture(self, community):
        """Returns 'dry' or 'wet' score 0–1."""
        if len(community) < 3: return 0
        vals = sorted([self._card_values(c) for c in community])
        flushy = len(set(c.suit for c in community)) <= 2
        connected = vals[-1] - vals[0] <= 4
        return 0.5*flushy + 0.5*connected
    
    def _estimate_equity_montecarlo(self, game_state, trials=1000):
        """Estimate hand equity via Monte Carlo simulation."""
        import random
        from poker_agents.card_utils import Card, Deck

        hole_cards = [Card(c) for c in self.hero['hole_cards']]
        community_cards = [Card(c) for c in game_state['community_cards']]
        num_opponents = len(game_state['other_player_moves'])

        wins = 0
        for _ in range(trials):
            deck = Deck()
            deck.remove_cards(hole_cards + community_cards)

            # Deal opponent hole cards
            opponent_holes = []
            for _ in range(num_opponents):
                opponent_holes.append([deck.draw(), deck.draw()])

            # Complete community cards
            needed_community = 5 - len(community_cards)
            sim_community = community_cards + [deck.draw() for _ in range(needed_community)]

            # Evaluate hands
            hero_rank = self._simple_hand_rank(hole_cards + sim_community)
            opponent_ranks = [self._simple_hand_rank(opp_hole + sim_community) for opp_hole in opponent_holes]

            if all(hero_rank > opp_rank for opp_rank in opponent_ranks):
                wins += 1

        return wins / trials

    def _simple_hand_rank(self, cards):
        """Very rough 5-card rank evaluator using counts and high card."""
        vals = [self._card_values(c) for c in cards]
        suits = [c.suit for c in cards]
        vals.sort(reverse=True)

        is_flush = len(set(suits)) == 1
        is_straight = len(set(vals)) == 5 and vals[0] - vals[-1] == 4

        counts = {v: vals.count(v) for v in vals}
        count_pattern = sorted(counts.values(), reverse=True)

        # Encode rank category + high-card tiebreakers
        if is_straight and is_flush:
            rank = (8, vals[0])                     # straight flush
        elif count_pattern == [4, 1]:
            rank = (7, max(counts, key=lambda x: counts[x]==4))
        elif count_pattern == [3, 2]:
            rank = (6, max(counts, key=lambda x: counts[x]==3))
        elif is_flush:
            rank = (5, *vals)
        elif is_straight:
            rank = (4, vals[0])
        elif count_pattern == [3, 1, 1]:
            rank = (3, max(counts, key=lambda x: counts[x]==3))
        elif count_pattern == [2, 2, 1]:
            pair_vals = sorted([v for v, c in counts.items() if c == 2], reverse=True)
            rank = (2, *pair_vals)
        elif count_pattern == [2, 1, 1, 1]:
            pair = max(counts, key=lambda x: counts[x]==2)
            rank = (1, pair, *vals)
        else:
            rank = (0, *vals)
        return rank


    def make_decision(self, game_state) -> Tuple[str, int]:
        import random
        call_required = self.call_required
        chips = self.stack
        pot = game_state['pot']
        community = game_state['community_cards']
        phase = game_state['game_phase']
        hole = self.hero['hole_cards']
        pos = getattr(self, 'position', 'mid')

        def bet_size(confidence: float) -> int:
            """Dynamic raise size scaled by confidence (0–1)."""
            return min(chips, max(1, int(pot * (0.25 + 0.75 * (confidence - 0.5)))))

        # --- PRE-FLOP STRATEGY ---
        a = self._card_values(hole[0])
        b = self._card_values(hole[1])
        is_pair = a == b
        is_suited = hole[0][-1] == hole[1][-1]
        gap = abs(a - b)

        if is_pair:
            base = 0.6 + a / 28.0
        elif is_suited:
            base = 0.3 + (14 - gap) / 28.0 * 0.4
        else:
            base = 0.2 + (14 - gap) / 28.0 * 0.3
        score = min(1.0, max(0.0, base))

        if pos == 'early': score -= 0.1
        elif pos == 'late': score += 0.1
        score = max(0.0, min(1.0, score))

        if phase == 'preflop':
            if call_required == 0:
                if score > 0.75: return self.raise_by(bet_size(score))
                elif score > 0.5: return self.check()
                else: return self.check()
            if call_required <= max(1, int(chips * 0.05)):
                if score > 0.45: return self.call()
            return self.fold()

        # --- POST-FLOP EQUITY DRIVEN LOGIC ---
        trials = 300 if phase == 'flop' else 200 if phase == 'turn' else 100
        equity = self._estimate_equity_montecarlo(game_state, trials=trials)
        pot_odds = 0 if call_required == 0 else call_required / (pot + call_required)
        texture = self._board_texture(community) if len(community) >= 3 else 0.0

        if call_required > 0:
            if equity > pot_odds + 0.08:
                if equity > 0.65 and chips > call_required * 3:
                    return self.raise_by(min(bet_size(equity), pot))
                return self.call()
            if texture > 0.6 and equity < 0.5:
                return self.fold()
            if pos == 'late' and 0.35 < equity < 0.55 and random.random() < 0.15:
                return self.call()
            return self.fold()
        else:
            if equity > 0.65:
                return self.raise_by(bet_size(equity))
            elif equity > 0.45:
                return self.check()
            elif 0.35 < equity < 0.55 and texture < 0.4 and random.random() < 0.25:
                return self.raise_by(max(1, int(pot * 0.4)))  # semi-bluff
            elif random.random() < (0.1 + 0.3 * (1 - texture)):
                return self.raise_by(max(1, int(pot * 0.25)))  # light bluff
            return self.check()

        
    def card_value(self, card):
        if card[:-1] == 'J':
            return 11
        elif card[:-1] == 'Q':
            return 12
        elif card[:-1] == 'K':
            return 13
        elif card[:-1] == 'A':
            return 14
        else:
            return int(card[:-1])
        
    def bet_size(confidence: float) -> int:
        """Dynamic raise size scaled by confidence (0–1)."""
        return min(chips, max(1, int(pot * (0.25 + 0.75 * (confidence - 0.5)))))
