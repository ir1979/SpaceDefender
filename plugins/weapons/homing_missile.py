"""Example weapon plugin: homing missile launcher."""

from __future__ import annotations

import math
from typing import List, TYPE_CHECKING

import pygame

from entities.base_entity import ShapeRenderer
from plugins.base import PluginMetadata, WeaponPlugin
from plugins.registry import register_weapon

if TYPE_CHECKING:
    from entities.player import Player


class HomingMissileProjectile(pygame.sprite.Sprite):
    """Simple homing missile projectile."""

    def __init__(
        self,
        x: int,
        y: int,
        damage: int,
        enemy_group: pygame.sprite.Group,
        speed: float = 7.0,
    ):
        super().__init__()
        self.damage = damage
        self.speed = speed
        self.turn_rate = 0.08
        self.velocity_x = 0.0
        self.velocity_y = -speed
        self.image = ShapeRenderer.create_shape(
            "triangle",
            (12, 20),
            (255, 170, 80),
        )
        self.rect = self.image.get_rect(center=(x, y))
        self.weapon_type = "homing_missile"
        self.angle = 0.0
        self.enemy_group = enemy_group

    def _find_target(self):
        best = None
        best_dist = float("inf")
        for sprite in self.enemy_group:
            if not hasattr(sprite, "enemy_type") or not getattr(sprite, "alive", lambda: True)():
                continue
            dx = sprite.rect.centerx - self.rect.centerx
            dy = sprite.rect.centery - self.rect.centery
            dist = dx * dx + dy * dy
            if dist < best_dist:
                best = sprite
                best_dist = dist
        return best

    def update(self):
        target = self._find_target()
        if target is not None:
            dx = target.rect.centerx - self.rect.centerx
            dy = target.rect.centery - self.rect.centery
            distance = math.hypot(dx, dy)
            if distance > 0:
                desired_x = (dx / distance) * self.speed
                desired_y = (dy / distance) * self.speed
                self.velocity_x += (desired_x - self.velocity_x) * self.turn_rate
                self.velocity_y += (desired_y - self.velocity_y) * self.turn_rate

        self.rect.x += int(self.velocity_x)
        self.rect.y += int(self.velocity_y)

        from config.settings import game_config

        if (
            self.rect.bottom < 0
            or self.rect.top > game_config.SCREEN_HEIGHT
            or self.rect.right < 0
            or self.rect.left > game_config.SCREEN_WIDTH
        ):
            self.kill()


class HomingMissileLauncherPlugin(WeaponPlugin):
    """Weapon plugin that fires homing missiles."""

    def __init__(self):
        super().__init__(
            PluginMetadata(
                plugin_id="homing_missile",
                name="Homing Missile Launcher",
                description="Fires missiles that track nearby enemies",
                author="plugin-example",
            )
        )

    def bullet_config(self):
        return {
            "type": "homing_missile",
            "shape": "triangle",
            "size": [12, 20],
            "color": [255, 170, 80],
            "speed": 7.0,
        }

    def get_cooldown(self, player: "Player") -> int:
        return 18

    def fire(self, player: "Player", bullet_factory: "BulletFactory") -> List[pygame.sprite.Sprite]:
        enemy_group = getattr(player, "enemy_group", None)
        if enemy_group is None:
            enemy_group = pygame.sprite.Group()
        missile = HomingMissileProjectile(
            player.rect.centerx,
            player.rect.top,
            player.damage + 25,
            enemy_group=enemy_group,
        )
        return [missile]


def register_plugin() -> None:
    register_weapon(HomingMissileLauncherPlugin(), replace=True)


register_plugin()
