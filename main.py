#!/usr/bin/env python3
"""
AI Poker Competition - Main Entry Point

This is the main entry point for the AI poker competition GUI.
It loads poker agents from the poker_agents folder and starts the game.
"""

import sys
import os
from game_manager import GameManager

def main():
    """Main entry point for the poker game"""
    print("AI Poker Competition")
    print("===================")
    print("Loading poker agents...")
    
    # Create and start the game manager with 1 second move interval
    game_manager = GameManager(move_interval=1.0)
    
    print(f"Loaded {len(game_manager.game_state.players)} players:")
    for i, player in enumerate(game_manager.game_state.players):
        print(f"  {i+1}. {player.name} (${player.chips} chips)")
    
    print("\nStarting game interface...")
    
    # Try to start GUI, fall back to CLI if not available
    if not game_manager.start_gui():
        print("GUI not available, starting command-line interface...")
        print("Use the CLI to manage the game:")
        print("- Choose options from the menu")
        print("- 'New Hand' to deal a new hand")
        print("- 'Next Phase' to advance the game (flop, turn, river)")
        print("- 'Player Action' for manual play")
        
        from poker_cli import PokerCLI
        cli = PokerCLI()
        cli.run()

if __name__ == "__main__":
    main()
