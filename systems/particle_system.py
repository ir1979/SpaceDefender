"""
Particle System Module
"""
import pygame
import random
import math
from typing import Tuple

class Particle(pygame.sprite.Sprite):
    """Visual particle effect"""
    
    def __init__(self, x: int, y: int, color: Tuple[int, int, int], 
                 velocity: Tuple[float, float], lifetime: int):
        super().__init__()
        self.color = color
        self.size = random.randint(2, 6)
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.velocity = velocity
        self.lifetime = lifetime
        self.age = 0
    
    def update(self):
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        self.age += 1
        
        alpha = int(255 * (1 - self.age / self.lifetime))
        self.image.set_alpha(alpha)
        
        if self.age >= self.lifetime:
            self.kill()

class ParticleSystem:
    """Manages particle effects"""
    
    def __init__(self):
        self.particles = pygame.sprite.Group()
    
    def emit_explosion(self, x: int, y: int, color: Tuple[int, int, int], count: int = 20):
        """Create an explosion effect"""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 5)
            velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
            lifetime = random.randint(20, 40)
            particle = Particle(x, y, color, velocity, lifetime)
            self.particles.add(particle)
    
    def emit_trail(self, x: int, y: int, color: Tuple[int, int, int]):
        """Create a trail effect"""
        velocity = (random.uniform(-1, 1), random.uniform(1, 3))
        lifetime = random.randint(10, 20)
        particle = Particle(x, y, color, velocity, lifetime)
        self.particles.add(particle)
    
    def update(self):
        self.particles.update()
    
    def draw(self, surface: pygame.Surface):
        self.particles.draw(surface)
