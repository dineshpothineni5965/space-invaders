import pygame


class Player:
    def __init__(self, x, y, width, height):
        self.x, self.y = float(x), float(y)
        self.width, self.height = width, height
        self.speed = 360  # pixels per second

    def move(self, dx, screen_width):
        self.x = max(0, min(self.x + dx, screen_width - self.width))

    def rect(self):
        return pygame.Rect(round(self.x), round(self.y), self.width, self.height)

    def center_x(self):
        return self.x + self.width / 2
