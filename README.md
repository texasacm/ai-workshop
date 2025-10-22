# AI Poker Competition

A GUI-based poker game system for AI agent competitions. Players can implement poker strategies as Python classes and compete against each other.

## Features

- **Text-based Card Rendering**: Cards are displayed as text (e.g., "Ace of Spades") instead of graphics
- **Oval Poker Table**: Visual representation of a poker table with players positioned around it
- **Autonomous AI Agents**: Agents play automatically with random strategies
- **Configurable Move Intervals**: Set timing between moves (default 1 second)
- **Real-time Game State**: Live updates of pot, community cards, player chips, and current actions
- **Complete Poker Logic**: Full hand evaluation, pot winning, and game flow
- **Agent Loading**: Automatically loads poker agents from the `poker_agents` folder
- **Game Logging**: Complete log of all game actions and decisions
- **Both GUI and CLI**: Visual interface with tkinter or command-line fallback

## Quick Start

1. **Run the game**:

   ```bash
   python main.py
   ```

2. **Use the GUI controls**:
   - Click "New Hand" to deal a new hand
   - Click "Next Phase" to advance through flop, turn, river
   - Click "Start Auto Play" to watch agents play autonomously
   - Adjust move interval for faster/slower gameplay
   - Watch the game log for all actions

## Creating Poker Agents

To create a poker agent, add a Python file to the `poker_agents` folder with the following structure:

```python
class PokerAgent:
    def __init__(self, name="Your Agent Name"):
        self.name = name
        self.chips = 1000

    def make_decision(self, game_state):
        # Implement your poker strategy here
        # Return one of: "fold", "call", "raise", "check"
        # For raise, you can also return the amount
        pass
```

### Game State Information

The `game_state` object contains:

- `players`: List of all players with their chips, cards, bets
- `community_cards`: List of community cards on the table
- `pot`: Current pot size
- `current_bet`: Current bet amount
- `game_phase`: Current phase (preflop, flop, turn, river, showdown)

## File Structure

```
ai-workshop/
├── main.py                 # Main entry point
├── game_manager.py         # Game logic and state management
├── poker_gui.py           # GUI implementation
├── requirements.txt       # Dependencies (none required)
├── README.md             # This file
└── poker_agents/         # Folder for AI agents
    ├── agent_1.py        # Sample agent 1
    ├── agent_2.py        # Sample agent 2
    ├── agent_3.py        # Sample agent 3
    └── agent_4.py        # Sample agent 4
```

## Game Flow

1. **Preflop**: Each player gets 2 hole cards, betting round
2. **Flop**: 3 community cards revealed, betting round
3. **Turn**: 1 more community card, betting round
4. **River**: Final community card, betting round
5. **Showdown**: Players reveal cards, winner determined

## GUI Components

- **Poker Table**: Oval table with players positioned around it
- **Player Widgets**: Show name, chips, cards, current bet, status, last action
- **Community Cards**: Display in the center of the table
- **Game Info**: Pot size, current phase, active player
- **Autonomous Controls**: Start/stop auto play, adjust move intervals
- **Game Log**: Scrollable log of all game events

## Text-Based Card Display

Cards are rendered as text rectangles showing:

- Rank (2, 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K, A)
- Suit symbol (♥, ♦, ♣, ♠)

Example: "Ace of Spades" appears as a rectangle with "A" and "♠"

## Development

The system is built with Python's standard library:

- `tkinter` for GUI
- `random` for card shuffling
- `enum` for card suits
- `typing` for type hints
- `importlib` for dynamic agent loading

No external dependencies required!
