"""
PowerUp Module
"""
import pygame
import math
import random
from typing import Dict, Any
from .base_entity import BaseEntity, ShapeRenderer
from config.settings import color_config

class PowerUp(BaseEntity):
    """Power-up collectible"""
    
    TYPES = {
        'rapid_fire': {
            'color': color_config.ORANGE,
            'shape': 'rectangle'
        },
        'shield': {
            'color': color_config.CYAN,
            'shape': 'circle'
        },
        'triple_shot': {
            'color': color_config.PURPLE,
            'shape': 'triangle'
        },
        'health': {
            'color': color_config.GREEN,
            'shape': 'diamond'
        }
    }
    
    def __init__(self, x: int, y: int, power_type: str):
        self.power_type = power_type
        config = self.TYPES.get(power_type, self.TYPES['health'])
        self.shape_type = config['shape']
        self.color = config['color']
        self.size = (30, 30)
        
        self.speed = 2
        self.bob_offset = 0
        self.bob_speed = 0.1
        
        super().__init__(x, y)
    
    def _create_image(self):
        """Create power-up visual"""
        self.image = ShapeRenderer.create_shape(
            self.shape_type, self.size, self.color)
    
    def update(self):
        """Update power-up"""
        self.rect.y += self.speed
        
        # Bobbing animation
        self.bob_offset += self.bob_speed
        self.rect.y += math.sin(self.bob_offset) * 2
        
        # Remove if off screen
        from config.settings import game_config
        if self.rect.top > game_config.SCREEN_HEIGHT:
            self.kill()
    
    def get_data(self) -> Dict[str, Any]:
        """Get power-up data"""
        data = super().get_data()
        data['power_type'] = self.power_type
        return data
