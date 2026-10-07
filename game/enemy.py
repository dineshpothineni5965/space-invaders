import pygame


class Enemy:
    def __init__(self, x, y, width=40, height=30):
        self.x, self.y = float(x), float(y)
        self.width, self.height = width, height
        self.alive = True

    def rect(self):
        return pygame.Rect(round(self.x), round(self.y), self.width, self.height)


class EnemyGrid:
    def __init__(self, screen_width, rows=4, cols=8, speed=90, drop_amount=20):
        self.screen_width, self.speed = screen_width, speed
        self.drop_amount, self.direction = drop_amount, 1
        self.enemies = [Enemy(40 + col * 55, 76 + row * 45)
                        for row in range(rows) for col in range(cols)]

    def alive_enemies(self):
        return [enemy for enemy in self.enemies if enemy.alive]

    def move(self, dt=1 / 60):
        alive = self.alive_enemies()
        if not alive:
            return
        dx = self.speed * self.direction * dt
        left = min(enemy.x for enemy in alive)
        right = max(enemy.x + enemy.width for enemy in alive)
        hit_edge = right + dx >= self.screen_width if dx > 0 else left + dx <= 0
        if hit_edge:
            # Reach the edge, drop once, and reverse.
            dx = self.screen_width - right if self.direction > 0 else -left
            self.direction *= -1
            for enemy in alive:
                enemy.y += self.drop_amount
        for enemy in alive:
            enemy.x += dx

    def reached_bottom(self, limit_y):
        return any(enemy.y + enemy.height >= limit_y for enemy in self.alive_enemies())
