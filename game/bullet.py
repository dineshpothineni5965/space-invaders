import pygame


class Bullet:
    def __init__(self, x, y, width=4, height=12, speed=480, direction=-1):
        self.x, self.y = float(x), float(y)
        self.previous_y = self.y
        self.width, self.height = width, height
        self.speed = speed  # pixels per second
        self.direction = direction

    def move(self, dt=1 / 60):
        self.previous_y = self.y
        self.y += self.speed * self.direction * dt

    def rect(self):
        return pygame.Rect(round(self.x), round(self.y), self.width, self.height)

    def swept_rect(self):
        """All pixels crossed this update; fast bullets cannot jump a target."""
        previous = pygame.Rect(round(self.x), round(self.previous_y), self.width, self.height)
        return previous.union(self.rect())

    def off_screen(self, screen_height):
        return self.y + self.height < 0 or self.y > screen_height
