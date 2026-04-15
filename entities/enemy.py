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
    
    def __init__(self, x: int, y: int, config: Dict[str, Any], target: Optional[BaseEntity] = None):
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
        self.target = target
        
        # Boss pulse effect
        self.base_size = self.size
        self.pulse_counter = 0.0
        self.pulse_speed = 0.08
        self.pulse_strength = 0.22
        
        # Freeze effect (freeze_timer > 0 means enemy is frozen)
        self.frozen_timer = 0
        # Slow effect (slow_timer > 0 means enemy is slowed)
        self.slow_timer = 0
        self.slow_factor = 1.0  # 1.0 = normal speed, <1.0 = slowed

        super().__init__(x, y)
    
    def _create_image(self):
        """Create enemy visual"""
        self.image = ShapeRenderer.create_shape(
            self.shape_type, self.size, self.color)
    
    def update(self):
        """Update enemy"""
        # Handle freeze timer
        if self.frozen_timer > 0:
            self.frozen_timer -= 1
            # Don't move or do anything while frozen
            from config.settings import game_config
            if self.rect.top > game_config.SCREEN_HEIGHT:
                self.kill()
            return

        # Handle slow timer
        if self.slow_timer > 0:
            self.slow_timer -= 1
            if self.slow_timer == 0:
                self.slow_factor = 1.0
        
        self.movement_counter += 1
        self._move()
        if self.enemy_type == 'boss':
            self._pulse()
        
        # Remove if off screen
        from config.settings import game_config
        if self.rect.top > game_config.SCREEN_HEIGHT:
            self.kill()
    
    def _move(self):
        """Move based on pattern"""
        effective_speed = self.speed * self.slow_factor
        from config.settings import game_config

        if self.enemy_type == 'boss':
            # Boss enters from above and then stays inside the screen.
            if self.rect.top < 80:
                self.rect.y += effective_speed
            else:
                self.rect.x += math.sin(self.movement_counter * 0.08) * 3 * self.slow_factor
                self.rect.y += math.sin(self.movement_counter * 0.05) * 1.5 * self.slow_factor

            if self.rect.left < 0:
                self.rect.left = 0
                self.direction = 1
            elif self.rect.right > game_config.SCREEN_WIDTH:
                self.rect.right = game_config.SCREEN_WIDTH
                self.direction = -1

            if self.rect.top < 0:
                self.rect.top = 0
            if self.rect.bottom > game_config.SCREEN_HEIGHT:
                self.rect.bottom = game_config.SCREEN_HEIGHT
            return

        if self.movement_pattern == 'straight':
            self.rect.y += effective_speed

        elif self.movement_pattern == 'sine':
            self.rect.y += effective_speed
            self.rect.x += math.sin(self.movement_counter * 0.1) * 3 * self.slow_factor

        elif self.movement_pattern == 'zigzag':
            self.rect.y += effective_speed
            if self.movement_counter % 30 == 0:
                self.direction *= -1
            self.rect.x += self.direction * 2 * self.slow_factor

        elif self.movement_pattern == 'spiral':
            angle = self.movement_counter * 0.1
            self.rect.x += math.cos(angle) * 2 * self.slow_factor
            self.rect.y += effective_speed

        elif self.movement_pattern == 'chase':
            self._chase(effective_speed)

        else:
            self.rect.y += effective_speed

    def _pulse(self):
        """Pulse boss size to draw attention."""
        self.pulse_counter += self.pulse_speed
        scale = 1.0 + math.sin(self.pulse_counter) * self.pulse_strength
        width = max(40, int(self.base_size[0] * scale))
        height = max(40, int(self.base_size[1] * scale))
        center = self.rect.center
        self.size = (width, height)
        self._create_image()
        self.rect = self.image.get_rect(center=center)

    def _chase(self, effective_speed: float):
        """Move toward the player target with a simple steering style."""
        if self.target and hasattr(self.target, 'rect'):
            dx = self.target.rect.centerx - self.rect.centerx
            dy = self.target.rect.centery - self.rect.centery
            distance = math.hypot(dx, dy)
            if distance > 0:
                self.rect.x += int((dx / distance) * effective_speed)
                self.rect.y += int((dy / distance) * effective_speed)
        else:
            self.rect.y += effective_speed

    def draw_health_bar(self, surface: pygame.Surface):
        """Draw health bar and freeze effect if applicable"""
        bar_width = self.rect.width
        bar_height = 5
        bar_x = self.rect.x
        bar_y = self.rect.y - 10

        if self.frozen_timer > 0:
            pygame.draw.rect(surface, color_config.CYAN,
                             (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(surface, color_config.WHITE,
                             (bar_x, bar_y, bar_width, bar_height), 1)
        elif self.slow_timer > 0:
            pygame.draw.rect(surface, color_config.PURPLE,
                             (bar_x, bar_y, bar_width, bar_height))
            health_width = int(bar_width * (self.health / self.max_health))
            pygame.draw.rect(surface, color_config.GREEN,
                             (bar_x, bar_y, health_width, bar_height))
            pygame.draw.rect(surface, color_config.WHITE,
                             (bar_x, bar_y, bar_width, bar_height), 1)
        else:
            if self.health >= self.max_health:
                return
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
                'size': [140, 140],
                'color': [255, 255, 50],
                'health': 400,
                'speed': 1.2,
                'movement': 'sine',
                'coin_value': 200,
                'score_value': 1500
            }
        }
    
    @classmethod
    def create(cls, enemy_type: str, x: int, y: int, 
               level: int = 1, target: Optional[BaseEntity] = None) -> Optional[Enemy]:
        """Create an enemy"""
        if not cls._enemy_configs:
            cls._create_default_configs()
        
        config = cls._enemy_configs.get(enemy_type)
        if not config:
            return None
        
        # Scale with level
        scaled_config = config.copy()
        if enemy_type == 'boss':
            scaled_config['health'] = int(config['health'] * (1 + level * 0.35))
            scaled_config['speed'] = max(0.9, config['speed'] * (1 + level * 0.02))
            scaled_config['coin_value'] = int(config['coin_value'] * (1 + level * 0.15))
            scaled_config['score_value'] = int(config['score_value'] * (1 + level * 0.15))
        else:
            scaled_config['health'] = int(config['health'] * (1 + level * 0.2))
            scaled_config['speed'] = config['speed'] * (1 + level * 0.05)
            scaled_config['coin_value'] = int(config['coin_value'] * (1 + level * 0.1))
            scaled_config['score_value'] = int(config['score_value'] * (1 + level * 0.1))
        
        return Enemy(x, y, scaled_config, target=target)
    
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
        non_boss_types = [t for t in types if t != 'boss']
        
        if level <= 2:
            return 'basic'
        elif level <= 5:
            return random.choice(['basic', 'basic', 'fast'])
        elif level <= 10:
            # Keep this list aligned with configured enemy types.
            mid_pool = [t for t in ['basic', 'fast', 'weaver', 'tank'] if t in types]
            return random.choice(mid_pool if mid_pool else non_boss_types if non_boss_types else types)
        else:
            return random.choice(non_boss_types if non_boss_types else types)
