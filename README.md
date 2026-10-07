# Space Invaders - completed lab (Problem 46)

A Python/Pygame windowed game launched from the terminal. Based on:
https://github.com/SETAPESU26/46_space-invaders

Original commit: `9ab47264972a4deeb6e9925e32c58b98e9f3b703`.

## Run

Use Python 3.10 or newer. Open a terminal inside this folder:

```bash
python -m pip install -r requirements.txt
python main.py
```

On systems where Python is named `python3`, use that instead.
A desktop display is required to play. No external images or sound files are
needed. Sound effects are generated when the game starts. If no audio device
is available, the game still runs and the menu says audio is unavailable.

## Controls

| Key | Action |
| --- | --- |
| 1 | Start/replay on Easy |
| 2 | Start/replay on Medium |
| 3 | Start/replay on Hard |
| Left / Right or A / D | Move |
| Space (tap or hold) | Fire |
| Q / Esc or window close | Exit |

Difficulty keys work on the title and result screens. They do not reset an
active round accidentally.

| Difficulty | Enemy speed, pixels/second | Firing rate per enemy, shots/second |
| --- | ---: | ---: |
| Easy | 60 | 0.10 |
| Medium | 90 | 0.24 |
| Hard | 150 | 0.48 |

Firing is random: these are target rates, not guarantees of a shot every fixed
interval. Total incoming fire also depends on the number of living enemies.

## What changed

1. **Collision detection:** a new survivor list replaces in-loop removal.
   Each bullet checks its previous-to-current swept rectangle, which catches
   a fast bullet crossing a target between frames. Collision detection runs
   before off-screen cleanup. A bullet destroys only the nearest enemy on its
   upward path, and each enemy can score only once.
2. **Game over:** a result screen retains the final score and loss reason.
   Enemy bullets hitting the player, or invaders reaching the player's defense
   line, end the round. Updating stops, but event handling and drawing continue.
3. **Replay:** one `reset(difficulty)` method restores the player, grid,
   direction, bullets, score, cooldown and result state. No recursive game loops.
4. **Sound:** original synthesized effects for firing, enemy destruction and
   game over. The game-over sound has a reserved audio channel.

Also added: a title menu, hold-to-fire, time-based movement, clean exit and a
victory screen when all enemies are destroyed.

## Code map

- `main.py`: window, event loop, time step and shutdown.
- `game/game_engine.py`: gameplay, collisions, state, menus and rendering.
- `game/player.py`: player position and screen bounds.
- `game/enemy.py`: enemy grid movement and edge drops.
- `game/bullet.py`: bullet movement and swept collision rectangle.
- `game/sound.py`: generated sound effects and optional audio output.
- `tests/test_game.py`: focused regression checks.
- `ASSIGNMENT.md`: unchanged original assignment instructions.

## Verify

```bash
python -m unittest discover -s tests -v
```

18 tests passed on Python 3.12 / Pygame 2.6.1, using offscreen SDL video and
SDL's dummy audio device. The recordings run the actual `main.py` event loop
with scripted key input. Local speaker output and your desktop keyboard still
need your own quick play-through.

Read `REVIEW_NOTES.md` for the original failing example and review questions.
