#!/usr/bin/env python3
"""
AI Poker Competition - Main Entry Point

This is the main entry point for the AI poker competition GUI.
It loads poker agents from the poker_agents folder and starts the game.
"""

import argparse
import sys
import os
from game_manager import GameManager
from poker_agents.agent_base import PokerAgentBase


def parse_args():
    parser = argparse.ArgumentParser(description="AI Poker Competition")
    parser.add_argument(
        "--max_hand_limit",
        type=int,
        default=None,
        help="Maximum number of hands before the tournament is forced to end.",
    )
    parser.add_argument(
        "--starting_chips",
        type=int,
        default=PokerAgentBase.STARTING_CHIPS,
        help="Starting chip stack for each player.",
    )
    parser.add_argument(
        "--move_interval",
        type=float,
        default=1.0,
        help="Seconds between autonomous moves in the GUI.",
    )
    return parser.parse_args()

def main():
    """Main entry point for the poker game"""
    args = parse_args()

    print("AI Poker Competition")
    print("===================")
    print("Loading poker agents...")
    
    # Create and start the game manager with 1 second move interval
    game_manager = GameManager(
        move_interval=args.move_interval,
        starting_chips=args.starting_chips,
        max_hand_limit=args.max_hand_limit,
    )
    
    print(f"Loaded {len(game_manager.game_state.players)} players:")
    for i, player in enumerate(game_manager.game_state.players):
        print(f"  {i+1}. {player.name} (${player.chips} chips)")

    if args.max_hand_limit:
        print(f"Maximum hand limit: {args.max_hand_limit}")
    
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
        cli = PokerCLI(
            move_interval=args.move_interval,
            starting_chips=args.starting_chips,
            max_hand_limit=args.max_hand_limit,
        )
        cli.run()

if __name__ == "__main__":
    main()
