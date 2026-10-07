import math
import random
import pygame
from .player import Player
from .enemy import EnemyGrid
from .bullet import Bullet
from .sound import SoundBank

BACKGROUND = (9, 15, 26)
WHITE, MUTED = (228, 237, 249), (143, 163, 186)
GREEN, RED, CYAN = (87, 235, 171), (255, 113, 129), (94, 201, 244)

# Enemy speed (pixels/second), per-enemy firing rate (shots/second).
DIFFICULTIES = {"Easy": (60, 0.10), "Medium": (90, 0.24), "Hard": (150, 0.48)}
DIFFICULTY_KEYS = {pygame.K_1: "Easy", pygame.K_2: "Medium", pygame.K_3: "Hard"}


class GameEngine:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.running = True
        self.sound = SoundBank()
        self.font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 22)
        self.title_font = pygame.font.Font(None, 52)
        self.reset("Medium")
        self.state = "menu"

    @property
    def game_over(self):
        return self.state == "game_over"

    def reset(self, difficulty):
        """A new round has no bullets, score, timers or flags from the last."""
        speed, self.enemy_fire_rate = DIFFICULTIES[difficulty]
        self.difficulty = difficulty
        self.player = Player(self.width // 2 - 20, self.height - 50, 40, 20)
        self.enemy_grid = EnemyGrid(self.width, speed=speed)
        self.player_bullets, self.enemy_bullets = [], []
        self._shoot_cooldown = 0.0
        self.score, self.reason, self.state = 0, "", "playing"

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                self.running = False
            elif self.state != "playing" and event.key in DIFFICULTY_KEYS:
                self.reset(DIFFICULTY_KEYS[event.key])
            elif self.state == "playing" and event.key == pygame.K_SPACE:
                self._fire()

    def handle_input(self, dt=1 / 60):
        if self.state != "playing":
            return
        keys = pygame.key.get_pressed()
        left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        self.player.move((int(right) - int(left)) * self.player.speed * dt, self.width)
        if keys[pygame.K_SPACE]:
            self._fire()

    def _fire(self):
        if self._shoot_cooldown <= 0:
            self.player_bullets.append(Bullet(self.player.center_x() - 2, self.player.y, direction=-1))
            self._shoot_cooldown = 0.18
            self.sound.play("fire")

    def _resolve_player_hits(self):
        # Build a new list; never remove from the list being traversed.
        remaining = []
        for bullet in self.player_bullets:
            targets = [enemy for enemy in self.enemy_grid.alive_enemies()
                       if bullet.swept_rect().colliderect(enemy.rect())]
            if targets:
                # An upward bullet hits the lowest intersected enemy first.
                target = max(targets, key=lambda enemy: enemy.y + enemy.height)
                target.alive = False
                self.score += 1
                self.sound.play("hit")
            elif not bullet.off_screen(self.height):
                remaining.append(bullet)
        self.player_bullets = remaining

    def _finish(self, reason, won=False):
        if self.state != "playing":
            return
        self.reason = reason
        self.state = "victory" if won else "game_over"
        self.sound.play("game_over")

    def update(self, dt=1 / 60):
        if self.state != "playing":
            return
        self._shoot_cooldown = max(0.0, self._shoot_cooldown - dt)
        self.enemy_grid.move(dt)
        # Equivalent firing probability at different frame rates.
        probability = 1 - math.exp(-self.enemy_fire_rate * dt)
        for enemy in self.enemy_grid.alive_enemies():
            if random.random() < probability:
                self.enemy_bullets.append(Bullet(enemy.x + enemy.width / 2 - 2,
                                                 enemy.y + enemy.height,
                                                 speed=300, direction=1))
        for bullet in self.player_bullets + self.enemy_bullets:
            bullet.move(dt)
        # Resolve hits BEFORE culling bullets outside the screen.
        self._resolve_player_hits()
        if any(bullet.swept_rect().colliderect(self.player.rect())
               for bullet in self.enemy_bullets):
            self._finish("Your ship was hit.")
        elif self.enemy_grid.reached_bottom(self.player.y):
            self._finish("The invaders reached your defense line.")
        elif not self.enemy_grid.alive_enemies():
            self._finish("All invaders destroyed!", won=True)
        self.enemy_bullets = [bullet for bullet in self.enemy_bullets
                              if not bullet.off_screen(self.height)]

    def _center(self, screen, text, y, font=None, color=WHITE):
        label = (font or self.font).render(text, True, color)
        screen.blit(label, label.get_rect(center=(self.width // 2, y)))

    def render(self, screen):
        screen.fill(BACKGROUND)
        for index in range(45):
            x, y = (index * 137 + 19) % self.width, (index * 83 + 47) % self.height
            pygame.draw.circle(screen, (30, 43, 60), (x, y), 1)
        pygame.draw.line(screen, (35, 53, 72), (18, 53), (self.width - 18, 53))
        screen.blit(self.font.render(f"SCORE  {self.score:02}", True, WHITE), (18, 17))
        difficulty = self.small_font.render(self.difficulty.upper(), True, CYAN)
        screen.blit(difficulty, (self.width - difficulty.get_width() - 18, 24))
        pygame.draw.line(screen, (35, 68, 62), (0, int(self.player.y + self.player.height + 5)),
                         (self.width, int(self.player.y + self.player.height + 5)))
        pygame.draw.rect(screen, GREEN, self.player.rect(), border_radius=4)
        pygame.draw.rect(screen, BACKGROUND, (round(self.player.x + 16), round(self.player.y + 9), 8, 9))
        for enemy in self.enemy_grid.alive_enemies():
            pygame.draw.rect(screen, CYAN, enemy.rect(), border_radius=3)
            pygame.draw.rect(screen, BACKGROUND, (round(enemy.x + 9), round(enemy.y + 9), 5, 6))
            pygame.draw.rect(screen, BACKGROUND, (round(enemy.x + 26), round(enemy.y + 9), 5, 6))
        for bullet in self.player_bullets:
            pygame.draw.rect(screen, GREEN, bullet.rect())
        for bullet in self.enemy_bullets:
            pygame.draw.rect(screen, RED, bullet.rect())
        self._center(screen, "ARROWS / A-D  move    SPACE  fire    Q / ESC  exit", self.height - 12,
                     self.small_font, MUTED)
        if self.state != "playing":
            shade = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            shade.fill((4, 8, 16, 205))
            screen.blit(shade, (0, 0))
            panel = pygame.Rect(42, 158, self.width - 84, 388)
            pygame.draw.rect(screen, (17, 28, 44), panel, border_radius=16)
            pygame.draw.rect(screen, (57, 83, 104), panel, width=1, border_radius=16)
            title = {"menu": "SPACE INVADERS", "game_over": "GAME OVER", "victory": "YOU WIN!"}[self.state]
            self._center(screen, title, 211, self.title_font, RED if self.game_over else GREEN)
            if self.state == "menu":
                self._center(screen, "Defend your line. Clear the invaders.", 259, self.small_font, MUTED)
                self._center(screen, "Choose your difficulty", 302)
            else:
                self._center(screen, self.reason, 259, self.small_font, MUTED)
                self._center(screen, f"FINAL SCORE  {self.score}", 298)
                self._center(screen, "Choose a difficulty to play again", 338, self.small_font, MUTED)
            for y, (label, description) in zip((380, 418, 456), (
                    ("1  EASY", "Slower enemies / less fire"),
                    ("2  MEDIUM", "Balanced speed / fire"),
                    ("3  HARD", "Faster enemies / more fire"))):
                screen.blit(self.small_font.render(label, True, GREEN), (81, y - 9))
                screen.blit(self.small_font.render(description, True, WHITE), (217, y - 9))
            self._center(screen, "Q / ESC  Exit", 506, self.small_font, MUTED)
            if not self.sound.available:
                self._center(screen, "Audio unavailable - playing silently", 576, self.small_font, MUTED)
