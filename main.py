"""Run with: python main.py (Python 3.10+)."""
import pygame
from game.game_engine import GameEngine

WIDTH, HEIGHT, FPS = 600, 700, 60


def main():
    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.init()
    try:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Space Invaders")
        clock = pygame.time.Clock()
        engine = GameEngine(WIDTH, HEIGHT)
        while engine.running:
            # Seconds, capped to avoid huge jumps after dragging the window.
            dt = min(clock.tick(FPS) / 1000.0, 0.05)
            for event in pygame.event.get():
                engine.handle_event(event)
            if not engine.running:
                break
            engine.handle_input(dt)
            engine.update(dt)
            engine.render(screen)
            pygame.display.flip()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
