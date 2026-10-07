# Debugging and review notes

These are the assistant's implementation and verification notes. They are not
a claim that the student has already performed their own critical review.

## Iteration 1 - reproduce the bug

The original loop calls `self.player_bullets.remove(bullet)` while iterating
over `self.player_bullets`. When item 0 is removed, item 1 moves to index 0,
but the iterator advances to index 1. That next bullet is skipped.

Reproduction: place two enemies at (100, 100) and (200, 100), each 40 x 30.
Place upward bullets at (110, 100) and (210, 100), moving 8 pixels per update.
Disable enemy movement and firing for this controlled regression test.
After moving, both bullet rectangles overlap their respective enemies by
four pixels. The original loop processes only the first collision.
On the following frame, the second bullet has already passed the enemy.

Observed after four updates:

| Version | Score | Enemies surviving | Bullets remaining |
| --- | ---: | ---: | ---: |
| Original starter | 1 | 1 | 1 |
| Fixed | 2 | 0 | 0 |

This controlled test is separate from the gameplay clips: those clips only
supply keyboard input and do not alter enemies, bullets, score or game state.

## Iteration 2 - make the collision fix complete

Iterating over a shallow copy would prevent skipped elements. Building a
survivor list also prevents the mutation and makes bullet cleanup explicit.
That alone does not fix tunneling: a fast bullet can be below a target in one
frame and above it in the next. `Bullet.swept_rect()` covers the old and new
positions. For these vertically moving bullets, this is the swept rectangular
path. Enemy hitboxes are evaluated at their updated positions; this is not a
general continuous-collision solver for arbitrarily moving objects.

Review also caught two edge cases to handle: do collision tests before removing
an off-screen bullet, and choose the nearest enemy if a fast shot crosses
several rows. Marking an enemy dead immediately prevents duplicate scoring.

## Iteration 3 - separate round state from application state

States: `menu`, `playing`, `game_over`, `victory`.

Only `playing` accepts ship controls or advances the simulation. Every state
still receives events and renders, so the result screen waits responsively.
Q, Escape and the window close button exit from any state. Difficulty keys
call one reset method rather than calling `main()` recursively.

The score, bullets, player, enemies, direction, cooldown and loss reason are
all reset together. Both defeat conditions and the clear-grid case have tests.

## Iteration 4 - audio and final verification

`SoundBank` generates signed 16-bit PCM effects and loads them into
`pygame.mixer.Sound`. No downloaded sound files are needed. Game-over audio
plays once on the transition into a result state. A missing sound device does
not crash the game.

18 regression tests pass. They cover simultaneous hits, tunneling, off-screen
cleanup order, nearest target, duplicate scoring, near misses, both loss
conditions, restart state, all difficulty keys, frozen controls after loss,
victory, hold-to-fire cooldown, player bounds, edge reversal, exit actions,
audio fallback and effect loading.

## Your critical review before submission

Run the game, listen for all three sound effects, and try all difficulties.
Then explain in your own words:

1. Why does removing from a list during iteration skip a bullet?
2. Why is a snapshot/survivor-list fix different from a swept collision fix?
3. Why must event handling continue when simulation updates stop?
4. Which state must reset when you replay, and what breaks if bullets remain?
5. Does Hard change both enemy speed and firing rate?

Tell the assistant what you observed or what you disagree with in this same
chat, so your actual review is part of the submitted history. Do not substitute
these notes for the required conversation link.

Reference APIs consulted:
- https://www.pygame.org/docs/ref/rect.html
- https://www.pygame.org/docs/ref/mixer.html
