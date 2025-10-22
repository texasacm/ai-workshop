#!/usr/bin/env python3
"""
Test script for the poker game logic
"""

from game_manager import GameManager, Card, Suit

def test_game_logic():
    """Test basic game logic without GUI"""
    print("Testing Poker Game Logic")
    print("========================")
    
    # Create game manager
    game = GameManager()
    
    print(f"Loaded {len(game.game_state.players)} players:")
    for player in game.game_state.players:
        print(f"  - {player.name}: ${player.chips} chips")
    
    # Test card creation
    print("\nTesting card creation:")
    ace_spades = Card("A", Suit.SPADES)
    king_hearts = Card("K", Suit.HEARTS)
    print(f"  {ace_spades}")
    print(f"  {king_hearts}")
    
    # Test deck creation
    print("\nTesting deck creation:")
    game.game_state.reset_deck()
    print(f"  Deck has {len(game.game_state.deck)} cards")
    
    # Test dealing cards
    print("\nTesting card dealing:")
    card1 = game.game_state.deal_card()
    card2 = game.game_state.deal_card()
    print(f"  Dealt: {card1}")
    print(f"  Dealt: {card2}")
    print(f"  Remaining cards: {len(game.game_state.deck)}")
    
    # Test starting a new hand
    print("\nTesting new hand:")
    game.start_new_hand()
    print(f"  Game phase: {game.game_state.game_phase}")
    print(f"  Community cards: {len(game.game_state.community_cards)}")
    
    for player in game.game_state.players:
        print(f"  {player.name}: {len(player.hole_cards)} cards, ${player.chips} chips")
    
    print("\nGame logic test completed successfully!")
    print("You can now run 'python main.py' to start the GUI")

if __name__ == "__main__":
    test_game_logic()
