"""Regression checks: python -m unittest discover -s tests -v"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import unittest
from unittest.mock import Mock, patch
import pygame
from game.bullet import Bullet
from game.enemy import Enemy, EnemyGrid
from game.game_engine import GameEngine, DIFFICULTIES
from game.sound import SoundBank, synthesize


class GameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.init()
        pygame.display.set_mode((600, 700))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        # Unit tests observe sound events without playing dozens of effects.
        with patch("game.game_engine.SoundBank"):
            self.game = GameEngine(600, 700)
        self.game.sound = Mock()
        self.game.reset("Medium")
        self.game.enemy_fire_rate = 0
        self.game.enemy_grid.speed = 0

    def enemies(self, *positions):
        self.game.enemy_grid.enemies = [Enemy(x, y) for x, y in positions]
        return self.game.enemy_grid.enemies

    def test_two_hits_same_frame_are_both_counted(self):
        enemies = self.enemies((100, 100), (200, 100))
        self.game.player_bullets = [Bullet(110, 100), Bullet(210, 100)]
        self.game.update()
        self.assertEqual(self.game.score, 2)
        self.assertTrue(all(not enemy.alive for enemy in enemies))
        self.assertEqual(self.game.player_bullets, [])

    def test_fast_bullet_cannot_tunnel_through_enemy(self):
        enemy, = self.enemies((100, 100))
        self.game.player_bullets = [Bullet(110, 155, speed=6000)]
        self.game.update()
        self.assertFalse(enemy.alive)
        self.assertEqual(self.game.score, 1)

    def test_collision_happens_before_offscreen_cleanup(self):
        enemy, = self.enemies((100, 40))
        self.game.player_bullets = [Bullet(110, 80, speed=6000)]
        self.game.update()
        self.assertFalse(enemy.alive)

    def test_one_bullet_hits_only_nearest_enemy(self):
        upper, lower = self.enemies((100, 100), (100, 160))
        self.game.player_bullets = [Bullet(110, 220, speed=12000)]
        self.game.update()
        self.assertTrue(upper.alive)
        self.assertFalse(lower.alive)
        self.assertEqual(self.game.score, 1)

    def test_two_bullets_cannot_score_same_enemy_twice(self):
        self.enemies((100, 100))
        self.game.player_bullets = [Bullet(110, 100), Bullet(110, 100)]
        self.game.update()
        self.assertEqual(self.game.score, 1)
        self.assertEqual(len(self.game.player_bullets), 1)

    def test_bullet_outside_enemy_width_does_not_hit(self):
        enemy, = self.enemies((100, 100))
        self.game.player_bullets = [Bullet(145, 155, speed=6000)]
        self.game.update()
        self.assertTrue(enemy.alive)
        self.assertEqual(self.game.score, 0)

    def test_enemy_bullet_ends_round_even_if_fast(self):
        self.game.score = 9
        self.game.enemy_bullets = [Bullet(290, 600, speed=7200, direction=1)]
        self.game.update()
        self.assertTrue(self.game.game_over)
        self.assertEqual(self.game.score, 9)
        self.assertIn("hit", self.game.reason)
        for _ in range(10):
            self.game.update()
        self.game.sound.play.assert_called_once_with("game_over")

    def test_enemies_reaching_defense_line_end_round(self):
        self.enemies((100, 620))
        self.game.update()
        self.assertTrue(self.game.game_over)
        self.assertIn("defense line", self.game.reason)

    def test_replay_resets_all_round_state_and_difficulty(self):
        self.game.score = 12
        self.game.player.x = 80
        self.game.player_bullets = [Bullet(10, 300)]
        self.game.enemy_bullets = [Bullet(40, 300)]
        self.game._shoot_cooldown = 0.15
        self.game.enemy_grid.enemies[0].alive = False
        self.game._finish("Test round complete")
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_3))
        self.assertEqual(self.game.state, "playing")
        self.assertEqual(self.game.score, 0)
        self.assertEqual(self.game.player.x, 280)
        self.assertEqual(self.game.player_bullets + self.game.enemy_bullets, [])
        self.assertEqual(self.game._shoot_cooldown, 0)
        self.assertEqual(len(self.game.enemy_grid.alive_enemies()), 32)
        self.assertEqual(self.game.enemy_grid.direction, 1)
        self.assertEqual(self.game.difficulty, "Hard")
        self.assertEqual((self.game.enemy_grid.speed, self.game.enemy_fire_rate), DIFFICULTIES["Hard"])

    def test_all_difficulty_keys_work_after_game_over(self):
        for key, name in ((pygame.K_1, "Easy"), (pygame.K_2, "Medium"), (pygame.K_3, "Hard")):
            self.game._finish("test")
            self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))
            self.assertEqual(self.game.difficulty, name)
            self.assertEqual((self.game.enemy_grid.speed, self.game.enemy_fire_rate), DIFFICULTIES[name])

    def test_game_over_blocks_movement_and_shooting(self):
        self.game._finish("test")
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        with patch("pygame.key.get_pressed") as get_keys:
            self.game.handle_input()
            get_keys.assert_not_called()
        self.assertEqual(self.game.player_bullets, [])

    def test_empty_grid_shows_victory_and_allows_replay(self):
        self.enemies()
        self.game.update()
        self.assertEqual(self.game.state, "victory")
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1))
        self.assertEqual(self.game.state, "playing")

    def test_held_space_obeys_cooldown_and_plays_firing_sound(self):
        class Keys:
            def __getitem__(self, key):
                return key == pygame.K_SPACE
        with patch("pygame.key.get_pressed", return_value=Keys()):
            for _ in range(12):
                self.game.handle_input()
                self.game.update()
        self.assertEqual(len(self.game.player_bullets), 2)
        self.assertEqual(self.game.sound.play.call_count, 2)

    def test_player_stays_inside_both_edges(self):
        self.game.player.move(-10000, 600)
        self.assertEqual(self.game.player.x, 0)
        self.game.player.move(10000, 600)
        self.assertEqual(self.game.player.x + self.game.player.width, 600)

    def test_enemy_grid_drops_once_then_reverses(self):
        grid = EnemyGrid(600)
        grid.enemies = [Enemy(559, 100)]
        grid.move()
        self.assertEqual(grid.enemies[0].x, 560)
        self.assertEqual(grid.enemies[0].y, 120)
        self.assertEqual(grid.direction, -1)
        grid.move()
        self.assertLess(grid.enemies[0].x, 560)
        self.assertEqual(grid.enemies[0].y, 120)

    def test_quit_works_from_each_screen(self):
        for state in ("menu", "playing", "game_over", "victory"):
            for event in (pygame.event.Event(pygame.QUIT),
                          pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE),
                          pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q)):
                self.game.running, self.game.state = True, state
                self.game.handle_event(event)
                self.assertFalse(self.game.running)

    def test_audio_failure_does_not_break_game(self):
        with patch("pygame.mixer.get_init", return_value=None):
            bank = SoundBank()
        self.assertFalse(bank.available)
        bank.play("fire")

    def test_effects_are_nonempty_and_load_in_mixer(self):
        bank = SoundBank()
        self.assertTrue(bank.available)
        for name in ("fire", "hit", "game_over"):
            self.assertGreater(max(abs(value) for value in synthesize(name)), 0)
            self.assertGreater(bank.sounds[name].get_length(), 0)


if __name__ == "__main__":
    unittest.main()
