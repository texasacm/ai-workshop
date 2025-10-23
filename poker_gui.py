import tkinter as tk
from tkinter import ttk, messagebox
import math
from typing import List, Optional

class CardWidget:
    """Widget for displaying a card as text"""
    def __init__(self, parent, card=None, width=80, height=110):
        self.parent = parent
        self.card = card
        self.width = width
        self.height = height
        self.frame = tk.Frame(parent, width=width, height=height, 
                             relief=tk.RAISED, bd=2, bg='white')
        self.frame.pack_propagate(False)
        self.frame.grid_propagate(False)
        self.label = tk.Label(
            self.frame,
            text=self._get_card_text(),
            font=('Helvetica', 16, 'bold'),
            bg='white',
            fg='black',
            justify='center'
        )
        self.label.config(wraplength=self.width - 12)
        self.label.pack(expand=True, fill='both', padx=6, pady=6)
    
    def _get_card_text(self):
        if self.card is None:
            return "??"
        return f"{self.card.rank}\n{self.card.suit.value}"
    
    def update_card(self, card):
        self.card = card
        self.label.config(text=self._get_card_text())
    
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.frame.grid(**kwargs)

class PlayerWidget:
    """Widget for displaying a player at the poker table"""
    def __init__(self, parent, player, position, total_positions):
        self.parent = parent
        self.player = player
        self.position = position
        self.total_positions = total_positions
        self.width = 180
        self.height = 165
        
        # Calculate position on the oval table
        angle = (2 * math.pi * position) / total_positions
        self.x = 200 + 150 * math.cos(angle)
        self.y = 200 + 100 * math.sin(angle)
        
        self.create_widget()
    
    def create_widget(self):
        # Player frame
        self.frame = tk.Frame(self.parent, bg='lightblue', relief=tk.RAISED, bd=2)
        self.frame.config(width=self.width, height=self.height)
        self.frame.pack_propagate(False)

        # Hand label (updated at showdown)
        self.hand_label = tk.Label(
            self.frame,
            text="",
            font=('Arial', 9, 'italic'),
            bg='lightblue',
            fg='black',
            wraplength=self.width - 10,
            justify='center'
        )
        self.hand_label.pack()
        
        # Player name
        self.name_label = tk.Label(self.frame, text=self.player.name, 
                                  font=('Arial', 10, 'bold'), bg='lightblue')
        self.name_label.pack()
        
        # Player chips
        self.chips_label = tk.Label(self.frame, text=f"${self.player.chips}", 
                                   font=('Arial', 9), bg='lightblue')
        self.chips_label.pack()
        
        # Player cards
        self.cards_frame = tk.Frame(self.frame, bg='lightblue')
        self.cards_frame.config(width=self.width - 20, height=110)
        self.cards_frame.pack_propagate(False)
        self.cards_frame.pack(pady=4)
        self.cards_frame.grid_columnconfigure(0, weight=1)
        self.cards_frame.grid_columnconfigure(1, weight=1)
        self.cards_frame.grid_rowconfigure(0, weight=1)

        self.card_widgets = []
        for i in range(2):
            card_widget = CardWidget(self.cards_frame, width=70, height=100)
            self.card_widgets.append(card_widget)
            card_widget.grid(row=0, column=i, padx=6, pady=2, sticky="n")

        # Last action label
        self.last_action_label = tk.Label(
            self.frame,
            text="",
            font=('Arial', 8, 'italic'),
            bg='lightblue'
        )
        self.last_action_label.pack(pady=2)

        # Current bet
        self.bet_label = tk.Label(self.frame, text="", font=('Arial', 8), bg='lightblue')
        self.bet_label.pack()
        
        # Status
        self.status_label = tk.Label(
            self.frame,
            text="",
            font=('Arial', 8),
            bg='lightblue',
            wraplength=self.width - 10,
            justify='center'
        )
        self.status_label.pack()
    
    def update_display(self):
        """Update the player display"""
        self.chips_label.config(text=f"${self.player.chips}")
        
        # Update cards - always show all cards (no hiding)
        for i, card_widget in enumerate(self.card_widgets):
            if i < len(self.player.hole_cards):
                card_widget.update_card(self.player.hole_cards[i])
            else:
                card_widget.update_card(None)

        # Show evaluated hand (if any)
        if self.player.best_hand_name:
            self.hand_label.config(text=self.player.best_hand_name)
        else:
            self.hand_label.config(text="")

        if self.player.last_action_display:
            self.last_action_label.config(text=self.player.last_action_display)
        else:
            self.last_action_label.config(text="")
        
        # Update bet display
        if self.player.current_bet > 0:
            self.bet_label.config(text=f"Bet: ${self.player.current_bet}")
        else:
            self.bet_label.config(text="")
        
        # Update status
        status = []
        if self.player.is_folded:
            status.append("FOLDED")
        if self.player.is_all_in:
            status.append("ALL IN")
        if self.player.chips <= 0:
            status.append("OUT OF CHIPS")
        if self.player.total_bet > 0:
            status.append(f"Total: ${self.player.total_bet}")
        if self.player.last_action:
            status.append(f"Last: {self.player.last_action.upper()}")
        
        self.status_label.config(text=" | ".join(status))
        
        # Set colors based on player status
        if getattr(self.player, "is_eliminated", False):
            # Grey out players who are eliminated from the game
            bg_color = 'lightgray'
            text_color = 'gray'
        elif hasattr(self.parent, 'current_player') and self.player == self.parent.current_player:
            # Highlight current player
            bg_color = 'yellow'
            text_color = 'black'
        else:
            # Normal player
            bg_color = 'lightblue'
            text_color = 'black'
        
        self.frame.config(bg=bg_color)
        self.name_label.config(bg=bg_color, fg=text_color)
        self.chips_label.config(bg=bg_color, fg=text_color)
        self.cards_frame.config(bg=bg_color)
        self.last_action_label.config(bg=bg_color, fg=text_color)
        self.bet_label.config(bg=bg_color, fg=text_color)
        self.status_label.config(bg=bg_color, fg=text_color)
        self.hand_label.config(bg=bg_color, fg=text_color)
    
    def place(self, x, y):
        """Place the widget at specific coordinates"""
        self.frame.place(x=x, y=y, width=self.width, height=self.height)

class PokerGUI:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.root = tk.Tk()
        self.root.title("AI Poker Competition")
        self.root.geometry("1000x700")
        self.root.configure(bg='darkgreen')
        
        self.player_widgets = []
        self.community_cards = []
        self.setup_ui()
        self.update_display()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main canvas for the poker table
        self.canvas = tk.Canvas(self.root, width=800, height=500, bg='darkgreen')
        self.canvas.pack(side=tk.TOP, padx=10, pady=10)
        
        # Draw poker table
        self.draw_poker_table()
        
        # Game info panel
        self.info_frame = tk.Frame(self.root, bg='lightgray')
        self.info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        # Pot display
        self.pot_label = tk.Label(self.info_frame, text="Pot: $0", 
                                 font=('Arial', 14, 'bold'), bg='lightgray')
        self.pot_label.pack(pady=5)
        
        # Game phase
        self.phase_label = tk.Label(self.info_frame, text="Phase: Preflop", 
                                   font=('Arial', 12), bg='lightgray')
        self.phase_label.pack(pady=5)
        
        # Current player
        self.current_player_label = tk.Label(self.info_frame, text="Current Player: None", 
                                           font=('Arial', 12), bg='lightgray')
        self.current_player_label.pack(pady=5)
        
        # Community cards
        self.community_frame = tk.Frame(self.info_frame, bg='lightgray')
        self.community_frame.pack(pady=10)
        
        community_label = tk.Label(self.community_frame, text="Community Cards:", 
                                  font=('Arial', 12, 'bold'), bg='lightgray')
        community_label.pack()
        
        self.community_cards_frame = tk.Frame(self.community_frame, bg='lightgray')
        self.community_cards_frame.pack()

        # Status / error message label
        self.message_label = tk.Label(
            self.info_frame,
            text="",
            font=('Arial', 9, 'bold'),
            fg='red',
            bg='lightgray',
            wraplength=260,
            justify='left'
        )
        self.message_label.pack(pady=5, fill=tk.X)
        
        # Control panel
        self.control_frame = tk.Frame(self.root, bg='lightgray')
        self.control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        
        # Game controls
        tk.Button(self.control_frame, text="New Hand", command=self.new_hand,
                 font=('Arial', 10, 'bold')).pack(pady=5, fill=tk.X)
        
        tk.Button(self.control_frame, text="Next Phase", command=self.next_phase,
                 font=('Arial', 10, 'bold')).pack(pady=5, fill=tk.X)
        
        # Autonomous play controls
        self.auto_frame = tk.Frame(self.control_frame, bg='lightgray')
        self.auto_frame.pack(pady=10)
        
        tk.Label(self.auto_frame, text="Autonomous Play:", 
                font=('Arial', 10, 'bold'), bg='lightgray').pack()
        
        self.auto_playing = False
        self.auto_button = tk.Button(self.auto_frame, text="Start Auto Play", 
                                   command=self.toggle_auto_play,
                                   font=('Arial', 9), bg='green')
        self.auto_button.pack(pady=5, fill=tk.X)
        
        # Move interval control
        interval_frame = tk.Frame(self.auto_frame, bg='lightgray')
        interval_frame.pack(pady=5)
        
        tk.Label(interval_frame, text="Move Interval (seconds):", bg='lightgray').pack()
        self.interval_var = tk.StringVar(value=str(self.game_manager.move_interval))
        self.interval_entry = tk.Entry(interval_frame, textvariable=self.interval_var, width=10)
        self.interval_entry.pack()
        
        tk.Button(interval_frame, text="Update Interval", 
                 command=self.update_interval, font=('Arial', 8)).pack(pady=2)
        
        # Log area
        self.log_frame = tk.Frame(self.root, bg='lightgray')
        self.log_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tk.Label(self.log_frame, text="Game Log:", 
                font=('Arial', 10, 'bold'), bg='lightgray').pack(anchor=tk.W)
        
        self.log_text = tk.Text(self.log_frame, height=8, width=80, 
                               font=('Courier', 9), bg='black', fg='green')
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.tag_configure("info", foreground="green")
        self.log_text.tag_configure("error", foreground="red")
        self.log_text.tag_configure("default", foreground="white")
        
        # Create player widgets
        self.create_player_widgets()
    
    def draw_poker_table(self):
        """Draw the poker table on the canvas"""
        # Draw oval table
        self.canvas.create_oval(50, 50, 750, 450, fill='darkgreen', outline='black', width=3)
        
        # Draw table center for community cards
        self.canvas.create_oval(300, 200, 500, 300, fill='lightgreen', outline='black', width=2)
    
    def create_player_widgets(self):
        """Create widgets for all players"""
        self.player_widgets = []
        players = self.game_manager.game_state.players
        
        for i, player in enumerate(players):
            # Calculate position around the table
            angle = (2 * math.pi * i) / len(players)
            x = 400 + 200 * math.cos(angle) - 50
            y = 250 + 150 * math.sin(angle) - 50
            
            player_widget = PlayerWidget(self.canvas, player, i, len(players))
            player_widget.place(x, y)
            self.player_widgets.append(player_widget)
    
    def update_display(self):
        """Update the entire display"""
        # Update pot
        self.pot_label.config(text=f"Pot: ${self.game_manager.game_state.pot}")
        
        # Update phase
        self.phase_label.config(text=f"Phase: {self.game_manager.game_state.game_phase.title()}")
        
        # Update current player
        if self.game_manager.game_state.current_player < len(self.game_manager.game_state.players):
            current_player = self.game_manager.game_state.players[self.game_manager.game_state.current_player]
            self.current_player_label.config(text=f"Current Player: {current_player.name}")
        else:
            self.current_player_label.config(text="Current Player: None")
        
        # Update community cards
        self.update_community_cards()
        
        # Update player widgets
        for widget in self.player_widgets:
            widget.update_display()

        note = self.game_manager.pop_last_action_note()
        if note:
            self.show_status_message(note, error=True)
            self.log_message(note, color="error")
        else:
            self.show_status_message("")
    
    def update_community_cards(self):
        """Update the community cards display"""
        # Clear existing community cards
        for widget in self.community_cards:
            widget.frame.destroy()
        self.community_cards = []
        
        # Create new community card widgets
        for card in self.game_manager.game_state.community_cards:
            card_widget = CardWidget(self.community_cards_frame, card, width=80, height=110)
            card_widget.pack(side=tk.LEFT, padx=2)
            self.community_cards.append(card_widget)
    
    def log_message(self, message, color="info"):
        """Add a message to the game log"""
        tag = "info" if color == "info" else "error" if color == "error" else "default"
        self.log_text.insert(tk.END, f"{message}\n", tag)
        self.log_text.see(tk.END)

    def show_status_message(self, message: str, error: bool = False):
        """Display transient feedback for invalid moves or other alerts."""
        if message:
            self.message_label.config(text=message, fg='red' if error else 'black')
        else:
            self.message_label.config(text="")
    
    def new_hand(self):
        """Start a new hand"""
        self.game_manager.start_new_hand()
        self.log_message("=== NEW HAND DEALT ===")
        self.update_display()
    
    def next_phase(self):
        """Move to the next game phase"""
        self.game_manager.next_phase()
        self.log_message(f"Phase changed to: {self.game_manager.game_state.game_phase}")
        self.update_display()
    
    def toggle_auto_play(self):
        """Toggle autonomous play on/off"""
        if self.auto_playing:
            self.auto_playing = False
            self.auto_button.config(text="Start Auto Play", bg='green')
            self.log_message("Autonomous play stopped")
        else:
            self.auto_playing = True
            self.auto_button.config(text="Stop Auto Play", bg='red')
            self.log_message("Autonomous play started")
            
            # Start a new hand if no hand is in progress
            if self.game_manager.game_state.game_phase == "showdown" or len(self.game_manager.game_state.players[0].hole_cards) == 0:
                self.game_manager.start_new_hand()
                self.log_message("=== NEW HAND DEALT ===")
                self.update_display()
            
            self.schedule_next_move()
    
    def update_interval(self):
        """Update the move interval"""
        try:
            interval = float(self.interval_var.get())
            if interval > 0:
                self.game_manager.move_interval = interval
                self.log_message(f"Move interval updated to {interval} seconds")
            else:
                self.log_message("Invalid interval (must be > 0)")
        except ValueError:
            self.log_message("Invalid interval format")
    
    def schedule_next_move(self):
        """Schedule the next autonomous move"""
        if self.auto_playing:
            self.root.after(int(self.game_manager.move_interval * 1000), self.play_autonomous_move)
    
    def play_autonomous_move(self):
        """Play one autonomous move"""
        if not self.auto_playing:
            return
        
        # Play one round
        continue_playing = self.game_manager.play_autonomous_round()
        
        # Update display
        self.update_display()
        
        # Schedule next move if still playing
        if continue_playing and self.auto_playing:
            self.schedule_next_move()
        else:
            # End of hand or game
            self.auto_playing = False
            self.auto_button.config(text="Start Auto Play", bg='green')
            if self.game_manager.game_state.game_phase == "showdown":
                self.log_message("Hand completed - check winners!")
    
    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()

if __name__ == "__main__":
    from game_manager import GameManager
    game = GameManager()
    gui = PokerGUI(game)
    gui.run()
