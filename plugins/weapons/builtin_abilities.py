"""Built-in weapon ability plugins mapped from legacy hardcoded logic."""

from __future__ import annotations

import math
import random
from typing import Any

from ..base import PluginMetadata, WeaponPlugin
from ..registry import register_weapon
from entities.bullet import BulletFactory
from config.settings import color_config


class AbilityWeaponPlugin(WeaponPlugin):
    """Convenience base for non-projectile active abilities."""

    trigger_mode = "ability"

    def __init__(self, plugin_id: str, name: str, description: str):
        super().__init__(
            PluginMetadata(
                plugin_id=plugin_id,
                name=name,
                description=description,
                author="core",
            )
        )

    def bullet_config(self):
        return {"type": self.plugin_id, "shape": "rectangle", "size": [1, 1], "color": [0, 0, 0], "speed": 0}


class AtomicBombAbility(AbilityWeaponPlugin):
    def __init__(self):
        super().__init__("atomic_bomb", "Atomic Bomb", "Destroy all enemies")

    def activate_ability(self, game: Any, player) -> bool:
        if not player.has_weapon("atomic_bomb"):
            return False
        game.assets.play_sound("explosion", 0.9)
        game.camera_shake_intensity = 15
        game.camera_shake_duration = 30
        game.atomic_bomb_flash = 200
        for enemy in list(game.enemies):
            player.coins += random.randint(5, 15)
            player.score += int(enemy.max_health * 10)
            if game.particle_system:
                game.particle_system.emit_explosion(
                    enemy.rect.centerx, enemy.rect.centery, color_config.YELLOW, count=15
                )
            enemy.kill()
        game.enemies.empty()
        return True


class EnemyFreezeAbility(AbilityWeaponPlugin):
    def __init__(self):
        super().__init__("enemy_freeze", "Enemy Freeze", "Freeze enemies")

    def activate_ability(self, game: Any, player) -> bool:
        if not player.has_weapon("enemy_freeze"):
            return False
        game.assets.play_sound("powerup", 0.7)
        for enemy in game.enemies:
            enemy.frozen_timer = 300
        return True


class ShockwaveAbility(AbilityWeaponPlugin):
    def __init__(self):
        super().__init__("shockwave", "Shockwave", "Area damage around player")

    def activate_ability(self, game: Any, player) -> bool:
        if not player.has_weapon("shockwave"):
            return False
        game.assets.play_sound("explosion", 0.8)
        game.camera_shake_intensity = 10
        game.camera_shake_duration = 20
        for enemy in list(game.enemies):
            dx = enemy.rect.centerx - player.rect.centerx
            dy = enemy.rect.centery - player.rect.centery
            dist = max(1.0, math.hypot(dx, dy))
            damage = max(10, int(150 / (dist / 50)))
            enemy.health -= damage
            enemy.rect.x += int(dx / dist * 80)
            enemy.rect.y += int(dy / dist * 80)
            if game.particle_system:
                game.particle_system.emit_explosion(
                    enemy.rect.centerx, enemy.rect.centery, color_config.CYAN, count=8
                )
            if enemy.health <= 0:
                player.coins += random.randint(5, 15)
                player.score += int(enemy.max_health * 10)
                enemy.kill()
        return True


class ChainLightningAbility(AbilityWeaponPlugin):
    def __init__(self):
        super().__init__("chain_lightning", "Chain Lightning", "Chain damage to nearby enemies")

    def activate_ability(self, game: Any, player) -> bool:
        if not player.has_weapon("chain_lightning"):
            return False
        game.assets.play_sound("powerup", 0.8)
        enemies = list(game.enemies)
        if not enemies:
            return True
        enemies.sort(
            key=lambda e: math.hypot(
                e.rect.centerx - player.rect.centerx,
                e.rect.centery - player.rect.centery,
            )
        )
        chain_damage = 80
        for enemy in enemies[:5]:
            enemy.health -= chain_damage
            if game.particle_system:
                game.particle_system.emit_explosion(
                    enemy.rect.centerx, enemy.rect.centery, color_config.YELLOW, count=12
                )
            if enemy.health <= 0:
                player.coins += random.randint(5, 15)
                player.score += int(enemy.max_health * 10)
                enemy.kill()
            chain_damage = int(chain_damage * 0.7)
        return True


class TimeWarpAbility(AbilityWeaponPlugin):
    def __init__(self):
        super().__init__("time_warp", "Time Warp", "Slow all enemies")

    def activate_ability(self, game: Any, player) -> bool:
        if not player.has_weapon("time_warp"):
            return False
        game.assets.play_sound("powerup", 0.7)
        for enemy in game.enemies:
            enemy.slow_timer = 300
            enemy.slow_factor = 0.25
            if game.particle_system:
                game.particle_system.emit_explosion(
                    enemy.rect.centerx, enemy.rect.centery, color_config.PURPLE, count=5
                )
        return True


class SpreadBurstAbility(AbilityWeaponPlugin):
    def __init__(self):
        super().__init__("spread_burst", "Spread Burst", "Fan burst of projectiles")

    def activate_ability(self, game: Any, player) -> bool:
        if not player.has_weapon("spread_burst"):
            return False
        game.assets.play_sound("shoot", 0.9)
        for angle in range(-55, 56, 10):
            bullet = BulletFactory.create(
                "default",
                player.rect.centerx,
                player.rect.top,
                -12,
                player.damage,
                angle,
            )
            if bullet:
                game.bullets.add(bullet)
                game.all_sprites.add(bullet)
                if game.particle_system:
                    game.particle_system.emit_trail(
                        bullet.rect.centerx, bullet.rect.centery, color_config.ORANGE
                    )
        return True


class MeteorStrikeAbility(AbilityWeaponPlugin):
    def __init__(self):
        super().__init__("meteor_strike", "Meteor Strike", "Heavy strike on random enemies")

    def activate_ability(self, game: Any, player) -> bool:
        if not player.has_weapon("meteor_strike"):
            return False
        game.assets.play_sound("explosion", 0.9)
        game.camera_shake_intensity = 12
        game.camera_shake_duration = 25
        game.atomic_bomb_flash = 120
        enemies = list(game.enemies)
        if not enemies:
            return True
        for enemy in random.sample(enemies, min(3, len(enemies))):
            enemy.health -= 150
            if game.particle_system:
                game.particle_system.emit_explosion(
                    enemy.rect.centerx, enemy.rect.centery, color_config.RED, count=25
                )
                game.particle_system.emit_explosion(
                    enemy.rect.centerx, enemy.rect.centery, color_config.ORANGE, count=20
                )
            if enemy.health <= 0:
                player.coins += random.randint(10, 25)
                player.score += int(enemy.max_health * 10)
                enemy.kill()
        return True


def register_builtin_weapon_abilities(register_fn=None) -> None:
    if register_fn is None:
        register_fn = register_weapon
    for plugin in [
        AtomicBombAbility(),
        EnemyFreezeAbility(),
        ShockwaveAbility(),
        ChainLightningAbility(),
        TimeWarpAbility(),
        SpreadBurstAbility(),
        MeteorStrikeAbility(),
    ]:
        register_fn(plugin, replace=True)


# Backward-compatible alias for earlier integration naming.
def register_builtin_ability_weapons(register_fn=None) -> None:
    register_builtin_weapon_abilities(register_fn)
