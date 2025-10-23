# AI Poker Workshop

Welcome to the AI Poker Workshop – a sandbox for teaching poker bots how to play Texas Hold ’em. The project ships with a simple GUI (tkinter) or CLI fallback, a handful of example agents, and the hooks you need to build your own strategy.

---

## What’s in the box?

| File / Folder            | Purpose |
|--------------------------|---------|
| `main.py`                | Entry point. Tries to launch the GUI; falls back to CLI when tkinter is missing. |
| `poker_cli.py`           | Menu-driven command-line interface. |
| `poker_gui.py`           | Tkinter table view, player widgets, logs, and auto-play controls. |
| `game_manager.py`        | Core game engine: shuffles, deals, tracks bets, evaluates hands, and mediates agent actions. |
| `poker_agents/agent_*.py`| Sample agents that demonstrate different play styles. |
| `poker_agents/agent_base.py` | Abstract base class every custom agent must subclass. |
| `poker_agents/agent_template.py` | Copy/paste starter file with scaffolding and comments. |

---

## Running the game

```bash
python main.py
``` 

*If the GUI fails with "No module named tkinter":*
1. macOS (Homebrew python):
   ```bash
   brew install python-tk
   ```
   or install the official python.org build (tkinter included).
2. Windows: tkinter ships with the standard installer—re-run the installer and include “tcl/tk”.
3. Linux (Debian/Ubuntu):
   ```bash
   sudo apt-get install python3-tk
   ```

Once tkinter is available, `main.py` launches the GUI. Without it, the CLI automatically starts.

---

## Building your own agent

1. Copy `poker_agents/agent_template.py` → `poker_agents/my_agent.py`.
2. Rename the class (or override `DEFAULT_NAME`) and fill in `make_decision`.
3. `GameManager` auto-loads any `PokerAgent` class in `poker_agents/` (except the base/template files), up to eight seats.

### Agent API recap

Every agent must subclass `PokerAgentBase` and implement:

```python
class PokerAgent(PokerAgentBase):
    def make_decision(self, game_state):
        ...
        return (action, amount)
```

Allowed `action` values (case-insensitive):

- `"fold"`
- `"check"`
- `"call"`
- `"raise"`
- `"all-in"` / `"shove"`

For `call` or `raise`, return a tuple `(action, amount)` where `amount` is the chips you want to commit. Unsupported actions (or numbers you can’t afford) cause the engine to automatically fold your agent.

### Visible game state

`game_state` is a dictionary with only public information:

- `self`: dict containing your chip stack, hole cards, committed bets, and `is_all_in` flag.
- `community_cards`: list of revealed board cards.
- `pot`: total chips in the middle.
- `current_bet`: highest bet any player has committed in the current round.
- `call_required`: chips you must add to match the current bet.
- `game_phase`: one of `preflop`, `flop`, `turn`, `river`, `showdown`.
- `other_player_moves`: list of `{"name", "last_action"}` for every opponent.
- `previous_player_action`: `{"name", "last_action"}` for the player who acted immediately before you (or `None` if you’re first).

Use this snapshot to decide your move—no direct access to other players’ cards or chip stacks.

---

## Playing with the sample agents

Run `python main.py` and use the GUI (“Start Auto Play”) to watch the four built-in agents:

1. **Agent 1** – shoves all-in every turn.
2. **Agent 2** – mirrors the previous player.
3. **Agent 3** – checks when possible, otherwise calls small bets.
4. **Agent 4** – coin-flip caller that instantly shoves with an Ace.

These demonstrate the decision API and the consequences of invalid moves (auto-fold). Use them as references when shaping your own strategies.

Happy hacking, and may the best bot win!
