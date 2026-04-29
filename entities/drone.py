"""
Drone helper module
"""

import math
import pygame
from typing import Optional
from .base_entity import BaseEntity, ShapeRenderer
from .bullet import BulletFactory
from config.settings import color_config


class Drone(BaseEntity):
    """Support drone that follows the player and fires at nearby enemies."""

    def __init__(self, player, level: int = 1, offset_x: int = 60):
        self.player = player
        self.level = max(1, min(5, level))
        self.shape_type = f"engine{self.level}"
        self.size = (32, 32)
        self.color = color_config.CYAN
        self.fire_cooldown = 0
        self.fire_rate = max(14, 42 - self.level * 4)
        self.bullet_damage = 6 + self.level * 2
        self.bullet_speed = -14 - self.level
        self.offset_x = offset_x
        self.offset_y = -(self.level - 3) * 14
        self._target_x = 0
        self._target_y = 0
        super().__init__(self.player.rect.centerx + self.offset_x,
                         self.player.rect.centery + self.offset_y)

    def _create_image(self):
        self.image = ShapeRenderer.create_shape(self.shape_type, self.size, self.color)

    def update(self):
        if not self.player:
            return

        self._target_x = self.player.rect.centerx + self.offset_x
        self._target_y = self.player.rect.centery + self.offset_y

        self.rect.centerx += int((self._target_x - self.rect.centerx) * 0.22)
        self.rect.centery += int((self._target_y - self.rect.centery) * 0.22)

    def try_fire(self, enemies: pygame.sprite.Group, bullets: pygame.sprite.Group, all_sprites: pygame.sprite.Group):
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
            return

        if not enemies or not bullets or not all_sprites:
            return

        closest_enemy = None
        min_distance = 9999
        for enemy in enemies:
            dx = enemy.rect.centerx - self.rect.centerx
            dy = enemy.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist < min_distance:
                closest_enemy = enemy
                min_distance = dist

        if closest_enemy is None or min_distance > 520:
            return

        bullet = BulletFactory.create(
            'default',
            self.rect.centerx,
            self.rect.centery,
            self.bullet_speed,
            self.bullet_damage,
            0,
            extra_config={'owner': 'player'}
        )
        if bullet:
            bullets.add(bullet)
            all_sprites.add(bullet)
            self.fire_cooldown = self.fire_rate
            # Small visual trail if available
            if hasattr(self.player, 'current_profile') and not getattr(self.player, 'network_controlled', False):
                pass
