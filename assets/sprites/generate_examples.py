#!/usr/bin/env python3
"""
Example sprite generator for Space Defender
This script creates simple PNG sprites for game artifacts.
Run this to generate example sprites that the game will use.
"""

import pygame
import os
from pathlib import Path

def create_sprite(name: str, width: int, height: int, color: tuple) -> pygame.Surface:
    """Create a simple sprite surface"""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Draw based on sprite type
    if 'spaceship' in name or 'fighter' in name:
        # Spaceship-like shapes
        points = [
            (width // 2, 0),
            (width, height),
            (width // 2, int(height * 0.7)),
            (0, height)
        ]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, (255, 255, 255), points, 2)
    
    elif 'bullet' in name:
        # Bullet shapes
        if 'laser' in name:
            pygame.draw.line(surface, color, (width//2, 0), (width//2, height), 3)
        else:
            pygame.draw.circle(surface, color, (width//2, height//2), min(width, height)//2)
            pygame.draw.circle(surface, (255, 255, 255), (width//2, height//2), min(width, height)//2, 1)
    
    elif 'enemy' in name:
        # Enemy shapes
        pygame.draw.rect(surface, color, (2, 2, width-4, height-4))
        pygame.draw.rect(surface, (255, 255, 255), (2, 2, width-4, height-4), 2)
        # Add eyes
        pygame.draw.circle(surface, (255, 255, 255), (width//3, height//3), 2)
        pygame.draw.circle(surface, (255, 255, 255), (2*width//3, height//3), 2)
    
    else:
        # Default shape
        pygame.draw.rect(surface, color, (0, 0, width, height))
        pygame.draw.rect(surface, (255, 255, 255), (0, 0, width, height), 2)
    
    return surface

def generate_examples():
    """Generate example sprites"""
    pygame.init()
    
    sprite_dir = Path(__file__).parent
    
    # Define sprites to generate
    sprites = {
        'spaceship': (50, 60, (0, 100, 255)),      # Blue
        'fighter': (50, 60, (100, 200, 255)),      # Light blue
        'bullet_basic': (6, 15, (255, 255, 50)),   # Yellow
        'bullet_laser': (4, 20, (50, 255, 255)),   # Cyan
        'bullet_plasma': (12, 12, (200, 50, 255)), # Purple
        'bullet_missile': (10, 18, (255, 150, 50)),# Orange
        'enemy_basic': (40, 40, (255, 50, 50)),    # Red
        'enemy_fast': (35, 35, (255, 150, 50)),    # Orange
        'enemy_tank': (60, 60, (200, 50, 255)),    # Purple
        'enemy_weaver': (45, 45, (50, 255, 255)),  # Cyan
        'enemy_boss': (80, 80, (255, 255, 50)),    # Yellow
    }
    
    print(f"Generating example sprites in {sprite_dir}/...")
    
    for sprite_name, (width, height, color) in sprites.items():
        # Create sprite
        surface = create_sprite(sprite_name, width, height, color)
        
        # Save as PNG
        filepath = sprite_dir / f"{sprite_name}.png"
        pygame.image.save(surface, str(filepath))
        print(f"  ✓ Created: {sprite_name}.png ({width}x{height}, {color})")
    
    pygame.quit()
    print("\nExample sprites created successfully!")
    print("The game will now use these sprites instead of procedural shapes.")
    print("You can replace these with your own custom PNG/SVG files.")

if __name__ == '__main__':
    generate_examples()
