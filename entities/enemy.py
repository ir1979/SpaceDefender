"""
Enemy Entity Module
Configurable enemies with different behaviors
"""
import pygame
import math
import random
from typing import Dict, Any, Optional
from .base_entity import BaseEntity, ShapeRenderer
from config.settings import color_config

class Enemy(BaseEntity):
    """Enemy entity with configurable behavior"""
    
    def __init__(self, x: int, y: int, config: Dict[str, Any]):
        self.config = config
        self.enemy_type = config.get('type', 'basic')
        self.shape_type = config.get('shape', 'rectangle')
        self.size = tuple(config.get('size', [40, 40]))
        self.color = tuple(config.get('color', color_config.RED))
        
        # Stats
        self.health = config.get('health', 30)
        self.max_health = self.health
        self.speed = config.get('speed', 2.0)
        self.coin_value = config.get('coin_value', 10)
        self.score_value = config.get('score_value', 100)
        
        # Movement
        self.movement_pattern = config.get('movement', 'straight')
        self.movement_counter = 0
        self.direction = random.choice([-1, 1])
        
        super().__init__(x, y)
    
    def _create_image(self):
        """Create enemy visual"""
        self.image = ShapeRenderer.create_shape(
            self.shape_type, self.size, self.color)
    
    def update(self):
        """Update enemy"""
        self.movement_counter += 1
        self._move()
        
        # Remove if off screen
        from config.settings import game_config
        if self.rect.top > game_config.SCREEN_HEIGHT:
            self.kill()
    
    def _move(self):
        """Move based on pattern"""
        if self.movement_pattern == 'straight':
            self.rect.y += self.speed
        
        elif self.movement_pattern == 'sine':
            self.rect.y += self.speed
            self.rect.x += math.sin(self.movement_counter * 0.1) * 3
        
        elif self.movement_pattern == 'zigzag':
            self.rect.y += self.speed
            if self.movement_counter % 30 == 0:
                self.direction *= -1
            self.rect.x += self.direction * 2
        
        elif self.movement_pattern == 'spiral':
            angle = self.movement_counter * 0.1
            radius = self.movement_counter * 0.5
            self.rect.x += math.cos(angle) * 2
            self.rect.y += self.speed
        
        elif self.movement_pattern == 'chase':
            # Would need player reference - placeholder
            self.rect.y += self.speed
    
    def draw_health_bar(self, surface: pygame.Surface):
        """Draw health bar"""
        if self.health >= self.max_health:
            return
        
        bar_width = self.rect.width
        bar_height = 5
        bar_x = self.rect.x
        bar_y = self.rect.y - 10
        
        pygame.draw.rect(surface, color_config.RED,
                        (bar_x, bar_y, bar_width, bar_height))
        
        health_width = int(bar_width * (self.health / self.max_health))
        pygame.draw.rect(surface, color_config.GREEN,
                        (bar_x, bar_y, health_width, bar_height))
    
    def get_data(self) -> Dict[str, Any]:
        """Get enemy data"""
        data = super().get_data()
        data.update({
            'enemy_type': self.enemy_type,
            'health': self.health,
            'shape_type': self.shape_type
        })
        return data

class EnemyFactory:
    """Factory for creating enemies from configuration"""
    
    _enemy_configs = {}
    
    @classmethod
    def load_configs(cls, config_file: str):
        """Load enemy configurations from JSON"""
        import json
        try:
            with open(config_file, 'r') as f:
                cls._enemy_configs = json.load(f)
        except FileNotFoundError:
            cls._create_default_configs()
    
    @classmethod
    def _create_default_configs(cls):
        """Create default enemy configs"""
        cls._enemy_configs = {
            'basic': {
                'type': 'basic',
                'shape': 'rectangle',
                'size': [40, 40],
                'color': [255, 50, 50],
                'health': 30,
                'speed': 2.0,
                'movement': 'straight',
                'coin_value': 10,
                'score_value': 100
            },
            'fast': {
                'type': 'fast',
                'shape': 'triangle',
                'size': [35, 35],
                'color': [255, 150, 50],
                'health': 20,
                'speed': 4.0,
                'movement': 'zigzag',
                'coin_value': 15,
                'score_value': 150
            },
            'tank': {
                'type': 'tank',
                'shape': 'circle',
                'size': [60, 60],
                'color': [200, 50, 255],
                'health': 80,
                'speed': 1.0,
                'movement': 'straight',
                'coin_value': 30,
                'score_value': 300
            },
            'weaver': {
                'type': 'weaver',
                'shape': 'diamond',
                'size': [45, 45],
                'color': [50, 255, 255],
                'health': 40,
                'speed': 2.5,
                'movement': 'sine',
                'coin_value': 20,
                'score_value': 200
            },
            'boss': {
                'type': 'boss',
                'shape': 'star',
                'size': [80, 80],
                'color': [255, 255, 50],
                'health': 200,
                'speed': 1.5,
                'movement': 'sine',
                'coin_value': 100,
                'score_value': 1000
            }
        }
    
    @classmethod
    def create(cls, enemy_type: str, x: int, y: int, 
               level: int = 1) -> Optional[Enemy]:
        """Create an enemy"""
        if not cls._enemy_configs:
            cls._create_default_configs()
        
        config = cls._enemy_configs.get(enemy_type)
        if not config:
            return None
        
        # Scale with level
        scaled_config = config.copy()
        scaled_config['health'] = int(config['health'] * (1 + level * 0.2))
        scaled_config['speed'] = config['speed'] * (1 + level * 0.05)
        scaled_config['coin_value'] = int(config['coin_value'] * (1 + level * 0.1))
        scaled_config['score_value'] = int(config['score_value'] * (1 + level * 0.1))
        
        return Enemy(x, y, scaled_config)
    
    @classmethod
    def get_available_types(cls):
        """Get available enemy types"""
        if not cls._enemy_configs:
            cls._create_default_configs()
        return list(cls._enemy_configs.keys())
    
    @classmethod
    def get_random_type(cls, level: int = 1):
        """Get random enemy type based on level"""
        types = cls.get_available_types()
        
        if level <= 2:
            return 'basic'
        elif level <= 5:
            return random.choice(['basic', 'basic', 'fast'])
        elif level <= 10:
            return random.choice(['basic', 'fast', 'weaver', 'tank'])
        else:
            return random.choice(types)
