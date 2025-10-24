#!/usr/bin/env python3
"""
Test autonomous poker gameplay
"""

from game_manager import GameManager

def test_autonomous_gameplay():
    """Test full autonomous gameplay"""
    print("Testing Autonomous Poker Gameplay")
    print("=" * 40)
    
    # Create game manager with 0.5 second intervals for faster testing
    game = GameManager(move_interval=0.5)
    
    print(f"Loaded {len(game.game_state.players)} players:")
    for player in game.game_state.players:
        print(f"  - {player.name}: ${player.chips} chips")
    
    print("\nStarting new hand...")
    game.start_new_hand()
    
    print(f"Game phase: {game.game_state.game_phase}")
    print("Community cards:", [str(card) for card in game.game_state.community_cards])
    
    for player in game.game_state.players:
        print(f"{player.name}: {[str(card) for card in player.hole_cards]} (${player.chips} chips)")
    
    print("\nPlaying autonomous rounds...")
    round_count = 0
    max_rounds = 100  # Prevent infinite loops
    
    while round_count < max_rounds:
        round_count += 1
        print(f"\n--- Round {round_count} ---")
        
        # Play one autonomous round
        continue_playing = game.play_autonomous_round()
        
        # Show current state
        print(f"Phase: {game.game_state.game_phase}")
        print(f"Pot: ${game.game_state.pot}")
        print(f"Current player: {game.game_state.players[game.game_state.current_player].name}")
        
        # Show player actions
        for player in game.game_state.players:
            status = []
            if player.is_folded:
                status.append("FOLDED")
            if player.is_all_in:
                status.append("ALL IN")
            if player.current_bet > 0:
                status.append(f"BET: ${player.current_bet}")
            if player.last_action:
                status.append(f"Last: {player.last_action}")
            
            status_str = f" ({', '.join(status)})" if status else ""
            print(f"  {player.name}: ${player.chips} chips{status_str}")
        
        if not continue_playing:
            print("Hand completed!")
            break
        
        # Small delay to see the progression
        import time
        time.sleep(0.1)
    
    print(f"\nCompleted {round_count} rounds")
    print("Autonomous gameplay test completed successfully!")

if __name__ == "__main__":
    test_autonomous_gameplay()
