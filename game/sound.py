"""Original arcade effects generated locally; no sound downloads needed."""
from array import array
from io import BytesIO
import math
import random
import sys
import wave
import pygame

SAMPLE_RATE = 44100


def synthesize(name):
    """Return signed 16-bit mono PCM, also used by the recording helper."""
    duration = {"fire": 0.09, "hit": 0.16, "game_over": 0.72}[name]
    samples = array("h")
    noise = random.Random(46)  # Independent of the gameplay random sequence.
    phase = 0.0
    for index in range(int(SAMPLE_RATE * duration)):
        t = index / SAMPLE_RATE
        fraction = t / duration
        envelope = min(t / 0.006, 1.0) * (1.0 - fraction) ** 1.5
        if name == "fire":
            frequency = 1100 - 750 * fraction
            phase += 2 * math.pi * frequency / SAMPLE_RATE
            value = math.sin(phase)
        elif name == "hit":
            phase += 2 * math.pi * (280 - 160 * fraction) / SAMPLE_RATE
            value = 0.6 * noise.uniform(-1, 1) + 0.4 * math.sin(phase)
        else:
            frequency = (392, 311, 196)[min(int(fraction * 3), 2)]
            phase += 2 * math.pi * frequency / SAMPLE_RATE
            value = math.sin(phase) + 0.2 * math.sin(phase * 2)
        samples.append(int(value * envelope * 9000))
    return samples


class SoundBank:
    def __init__(self):
        self.sounds = {}
        self.available = pygame.mixer.get_init() is not None
        if not self.available:
            return
        try:
            for name in ("fire", "hit", "game_over"):
                raw = synthesize(name)
                if sys.byteorder != "little":
                    raw.byteswap()
                data = BytesIO()
                with wave.open(data, "wb") as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(SAMPLE_RATE)
                    wav.writeframes(raw.tobytes())
                data.seek(0)
                self.sounds[name] = pygame.mixer.Sound(file=data)
            pygame.mixer.set_num_channels(16)
            pygame.mixer.set_reserved(1)
        except (pygame.error, OSError):
            self.available = False
            self.sounds.clear()

    def play(self, name):
        sound = self.sounds.get(name)
        if sound is None:
            return
        if name == "game_over":
            pygame.mixer.Channel(0).play(sound)
        else:
            sound.play()
