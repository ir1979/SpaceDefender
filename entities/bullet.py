"""
Bullet/Projectile Module
Configurable weapons and projectiles
"""
import pygame
import math
from typing import Dict, Any, Optional
from .base_entity import BaseEntity, ShapeRenderer
from config.settings import color_config

class Bullet(BaseEntity):
    """Projectile entity"""
    
    def __init__(self, x: int, y: int, config: Dict[str, Any], 
                 damage: int, angle: float = 0):
        self.config = config
        self.weapon_type = config.get('type', 'default')
        self.shape_type = config.get('shape', 'rectangle')
        self.size = tuple(config.get('size', [6, 15]))
        self.color = tuple(config.get('color', color_config.YELLOW))
        self.speed = config.get('speed', 10.0)
        
        self.damage = damage
        self.angle = angle
        
        # Calculate velocity - speed parameter controls direction
        angle_rad = math.radians(angle)
        self.velocity_x = math.sin(angle_rad) * abs(self.speed) * 0.3
        self.velocity_y = self.speed  # Use speed directly (negative = up, positive = down)
        
        super().__init__(x, y)
    
    def _create_image(self):
        """Create bullet visual"""
        self.image = ShapeRenderer.create_shape(
            self.shape_type, self.size, self.color)
        
        # Rotate if needed
        if self.angle != 0:
            self.image = pygame.transform.rotate(self.image, -self.angle)
    
    def update(self):
        """Update bullet position"""
        self.rect.y += self.velocity_y
        self.rect.x += self.velocity_x
        
        # Remove if off screen
        from config.settings import game_config
        if (self.rect.bottom < 0 or self.rect.top > game_config.SCREEN_HEIGHT or
            self.rect.right < 0 or self.rect.left > game_config.SCREEN_WIDTH):
            self.kill()
    
    def get_data(self) -> Dict[str, Any]:
        """Get bullet data"""
        data = super().get_data()
        data.update({
            'weapon_type': self.weapon_type,
            'damage': self.damage,
            'angle': self.angle,
            'speed': self.speed
        })
        return data

class BulletFactory:
    """Factory for creating bullets from configuration"""
    
    _weapon_configs = {}
    
    @classmethod
    def load_configs(cls, config_file: str):
        """Load weapon configurations"""
        import json
        try:
            with open(config_file, 'r') as f:
                cls._weapon_configs = json.load(f)
        except FileNotFoundError:
            cls._create_default_configs()
    
    @classmethod
    def _create_default_configs(cls):
        """Create default weapon configs"""
        cls._weapon_configs = {
            'default': {
                'type': 'default',
                'shape': 'rectangle',
                'size': [6, 15],
                'color': [255, 255, 50],
                'speed': 10.0
            },
            'laser': {
                'type': 'laser',
                'shape': 'rectangle',
                'size': [4, 20],
                'color': [50, 255, 255],
                'speed': 15.0
            },
            'plasma': {
                'type': 'plasma',
                'shape': 'circle',
                'size': [12, 12],
                'color': [200, 50, 255],
                'speed': 8.0
            },
            'missile': {
                'type': 'missile',
                'shape': 'triangle',
                'size': [10, 18],
                'color': [255, 150, 50],
                'speed': 7.0
            }
        }
    
    @classmethod
    def create(cls, weapon_type: str, x: int, y: int, 
               speed: float, damage: int, angle: float = 0) -> Optional[Bullet]:
        """Create a bullet"""
        if not cls._weapon_configs:
            cls._create_default_configs()
        
        config = cls._weapon_configs.get(weapon_type, cls._weapon_configs['default'])
        config_copy = config.copy()
        config_copy['speed'] = speed
        
        return Bullet(x, y, config_copy, damage, angle)
    
    @classmethod
    def get_available_types(cls):
        """Get available weapon types"""
        if not cls._weapon_configs:
            cls._create_default_configs()
        return list(cls._weapon_configs.keys())
