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

# FEATURE: Enemy Entity
class Enemy(BaseEntity):
    """Enemy entity with configurable behavior"""
    
    def __init__(self, x: int, y: int, config: Dict[str, Any], target: Optional[BaseEntity] = None):
        self.config = config
        self.enemy_type = config.get('type', 'basic')
        shape_config = config.get('shape', 'rectangle')
        if isinstance(shape_config, list):
            self.shape_type = random.choice(shape_config)
        elif shape_config == 'random_enemy':
            self.shape_type = self._choose_random_sprite_shape()
        else:
            self.shape_type = shape_config
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
        self.boss_phase = 1 if self.enemy_type == 'boss' else 0
        
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

    def _choose_random_sprite_shape(self):
        """Select a random enemy sprite shape from the loaded asset manager."""
        if ShapeRenderer.asset_manager:
            enemy_options = [
                name for name in ShapeRenderer.asset_manager.sprites
                if name.startswith('enemy')
            ]
            if enemy_options:
                return random.choice(enemy_options)
        return 'rectangle'
    
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

        elif self.movement_pattern == 'swoop':
            self.rect.y += effective_speed
            self.rect.x += math.sin(self.movement_counter * 0.12) * 4 * self.slow_factor
            if self.movement_counter % 50 == 0:
                self.direction *= -1
            self.rect.x += self.direction * 1 * self.slow_factor

        elif self.movement_pattern == 'drift':
            self.rect.y += effective_speed * 0.95
            self.rect.x += self.direction * 1.4 * self.slow_factor
            self.rect.y += math.sin(self.movement_counter * 0.07) * 1.5 * self.slow_factor
            if self.movement_counter % 80 == 0:
                self.direction = random.choice([-1, 1])

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

        health_ratio = self.health / max(1, self.max_health)
        if self.boss_phase == 1 and health_ratio < 0.7:
            self.boss_phase = 2
            self.speed *= 1.15
            self.pulse_strength += 0.12
        elif self.boss_phase == 2 and health_ratio < 0.35:
            self.boss_phase = 3
            self.speed *= 1.2
            self.pulse_speed += 0.06
            self.color = tuple(min(255, c + 20) for c in self.color)

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
                'shape': ['enemyRed2', 'enemyRed3', 'enemyRed4', 'enemyRed5', 'enemy_basic'],
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
                'shape': ['enemyBlue3', 'enemyBlue4', 'enemyBlue5', 'enemy_fast'],
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
                'shape': ['enemyBlack1', 'enemyBlack2', 'enemyBlack3', 'enemyBlack4', 'enemyBlack5', 'enemy_tank'],
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
                'shape': ['enemyGreen2', 'enemyGreen3', 'enemyGreen4', 'enemyGreen5', 'enemy_weaver'],
                'size': [45, 45],
                'color': [50, 255, 255],
                'health': 40,
                'speed': 2.5,
                'movement': 'sine',
                'coin_value': 20,
                'score_value': 200
            },
            'hunter': {
                'type': 'hunter',
                'shape': ['enemy_fast', 'enemyGreen3', 'enemyRed3', 'enemyBlue4'],
                'size': [42, 42],
                'color': [150, 255, 150],
                'health': 35,
                'speed': 2.2,
                'movement': 'chase',
                'coin_value': 25,
                'score_value': 220
            },
            'swarmer': {
                'type': 'swarmer',
                'shape': ['enemyBlue3', 'enemyRed4', 'enemyBlack2'],
                'size': [30, 30],
                'color': [220, 220, 60],
                'health': 18,
                'speed': 3.5,
                'movement': 'swoop',
                'coin_value': 12,
                'score_value': 120
            },
            'sentinel': {
                'type': 'sentinel',
                'shape': ['enemyGreen4', 'enemyGreen5', 'enemyBlue5'],
                'size': [50, 50],
                'color': [100, 200, 255],
                'health': 55,
                'speed': 1.8,
                'movement': 'drift',
                'coin_value': 28,
                'score_value': 260
            },
            'assassin': {
                'type': 'assassin',
                'shape': ['enemyRed2', 'enemyRed5', 'enemyBlue4'],
                'size': [42, 42],
                'color': [180, 255, 150],
                'health': 28,
                'speed': 3.0,
                'movement': 'chase',
                'coin_value': 30,
                'score_value': 280
            },
            'boss': {
                'type': 'boss',
                'shape': ['enemy_boss', 'enemy_boss_old', 'ufoRed', 'ufoYellow', 'ufoGreen'],
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
            scaled_config['health'] = int(config['health'] * (1 + level * 0.25))
            scaled_config['speed'] = config['speed'] * (1 + level * 0.06)
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
    def get_random_type(cls, level: int = 1, wave_number: int = 1):
        """Get random enemy type based on level and wave progression."""
        if not cls._enemy_configs:
            cls._create_default_configs()
        base_pool = []

        if level <= 2:
            base_pool = ['basic', 'fast', 'swarmer']
        elif level <= 5:
            base_pool = ['basic', 'fast', 'weaver', 'swarmer', 'assassin']
        elif level <= 10:
            base_pool = ['basic', 'fast', 'weaver', 'tank', 'hunter', 'swarmer', 'assassin', 'sentinel']
        else:
            base_pool = [t for t in cls.get_available_types() if t != 'boss']

        # Increase threat variety in later waves
        wave_bonus = []
        if wave_number > 1:
            wave_bonus.extend(['fast', 'hunter'])
        if wave_number > 2:
            wave_bonus.extend(['assassin', 'tank'])
        if wave_number > 4:
            wave_bonus.extend(['sentinel', 'dodge_bot'])
        if wave_number > 5:
            wave_bonus.extend(['teleporter'])

        if wave_bonus:
            base_pool.extend(wave_bonus)

        # Add a small chance for tougher enemies even in early stages
        if level >= 3:
            base_pool.extend(['weaver', 'assassin'])
        if level >= 6:
            base_pool.extend(['tank', 'hunter'])

        if not base_pool:
            base_pool = [t for t in cls.get_available_types() if t != 'boss']
        if not base_pool:
            base_pool = cls.get_available_types()

        return random.choice(base_pool)
