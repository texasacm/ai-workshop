#!/usr/bin/env python3
"""
Command-line poker game for environments without GUI
"""

from game_manager import GameManager, Card, Suit

class PokerCLI:
    def __init__(self):
        self.game = GameManager()
        self.running = True
    
    def display_game_state(self):
        """Display current game state"""
        print("\n" + "="*60)
        print(f"POT: ${self.game.game_state.pot}")
        print(f"PHASE: {self.game.game_state.game_phase.upper()}")
        print(f"CURRENT PLAYER: {self.game.game_state.players[self.game.game_state.current_player].name}")
        print("="*60)
        
        # Display community cards
        if self.game.game_state.community_cards:
            print("COMMUNITY CARDS:")
            for i, card in enumerate(self.game.game_state.community_cards):
                print(f"  {i+1}. {card}")
        else:
            print("COMMUNITY CARDS: None yet")
        
        print("\nPLAYERS:")
        for i, player in enumerate(self.game.game_state.players):
            status = []
            if player.is_folded:
                status.append("FOLDED")
            if player.is_all_in:
                status.append("ALL IN")
            if getattr(player, "is_eliminated", False):
                status.append("ELIMINATED")
            if player.current_bet > 0:
                status.append(f"BET: ${player.current_bet}")
            
            status_str = f" ({', '.join(status)})" if status else ""
            
            print(f"  {i+1}. {player.name}: ${player.chips} chips{status_str}")
            if player.hole_cards and not player.is_folded:
                print(f"     Cards: {[str(card) for card in player.hole_cards]}")
            if player.best_hand_name:
                print(f"     Best Hand: {player.best_hand_name}")
            if player.last_action_display:
                print(f"     Last Move: {player.last_action_display}")
    
    def show_menu(self):
        """Show the main menu"""
        print("\n" + "="*40)
        print("POKER GAME MENU")
        print("="*40)
        print("1. New Hand")
        print("2. Next Phase")
        print("3. Play Autonomous Round")
        print("4. Show Game State")
        print("5. Quit")
        print("="*40)
    
    def player_action_menu(self):
        """Show player action menu"""
        current_player = self.game.game_state.players[self.game.game_state.current_player]
        print(f"\n{current_player.name}'s turn:")
        print("1. Fold")
        print("2. Call")
        print("3. Check")
        print("4. Raise")
        print("5. Back to main menu")
        
        choice = input("Choose action (1-5): ").strip()
        
        if choice == "1":
            success = self.game.player_action(self.game.game_state.current_player, "fold")
            self._handle_action_result(success, f"{current_player.name} folded")
        elif choice == "2":
            success = self.game.player_action(self.game.game_state.current_player, "call")
            self._handle_action_result(success, f"{current_player.name} called")
        elif choice == "3":
            success = self.game.player_action(self.game.game_state.current_player, "check")
            self._handle_action_result(success, f"{current_player.name} checked")
        elif choice == "4":
            try:
                amount = int(input("Raise amount: $"))
                success = self.game.player_action(self.game.game_state.current_player, "raise", amount)
                self._handle_action_result(
                    success,
                    f"{current_player.name} raised by ${amount}",
                    "Invalid raise amount",
                )
            except ValueError:
                print("Invalid amount")
        elif choice == "5":
            return
        else:
            print("Invalid choice")
    
    def play_autonomous_round(self):
        """Play one autonomous round"""
        print("Playing autonomous round...")
        continue_playing = self.game.play_autonomous_round()
        self.display_game_state()
        self._report_last_note()
        
        if not continue_playing:
            print("Round completed!")
    
    def next_player(self):
        """Move to next player"""
        self.game.game_state.current_player = (self.game.game_state.current_player + 1) % len(self.game.game_state.players)

    def _handle_action_result(self, success, success_message=None, failure_message=None):
        """Print action outcomes and advance to the next player when needed."""
        note = self.game.pop_last_action_note()
        if note:
            print(f"!!! {note}")
        elif success and success_message:
            print(success_message)
        elif not success and failure_message:
            print(failure_message)

        if success:
            self.next_player()

    def _report_last_note(self):
        """Print any deferred engine notes (e.g., invalid move auto-folds)."""
        note = self.game.pop_last_action_note()
        if note:
            print(f"!!! {note}")
    
    def run(self):
        """Run the CLI game"""
        print("AI Poker Competition - Command Line Interface")
        print("=" * 50)
        
        while self.running:
            self.show_menu()
            choice = input("Choose option (1-5): ").strip()
            
            if choice == "1":
                self.game.start_new_hand()
                print("New hand dealt!")
                self.display_game_state()
            elif choice == "2":
                self.game.next_phase()
                print(f"Phase changed to: {self.game.game_state.game_phase}")
                self.display_game_state()
            elif choice == "3":
                self.play_autonomous_round()
            elif choice == "4":
                self.display_game_state()
            elif choice == "5":
                print("Thanks for playing!")
                self.running = False
            else:
                print("Invalid choice, please try again")

if __name__ == "__main__":
    cli = PokerCLI()
    cli.run()
