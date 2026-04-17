"""Plugin base classes for Space Defender extensibility."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    import pygame

    from entities.bullet import Bullet, BulletFactory
    from entities.enemy import Enemy
    from entities.player import Player
    from systems.save_system import PlayerProfile
    from ui.menus import Shop


@dataclass
class PluginMetadata:
    """Common metadata for all plugin types."""

    plugin_id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    author: str = "core"
    icon: Optional[str] = None


@dataclass
class ShopItemDefinition:
    """Serializable shop item description used by shop UI."""

    id: str
    name: str
    description: str
    base_cost: int
    max_level: int = 1
    order: int = 1000
    icon: Optional[str] = None


@dataclass
class ShopPurchaseContext:
    """Runtime context passed to shop item plugins."""

    shop: "Shop"
    player: "Player"
    profile: Optional["PlayerProfile"]
    item: Dict[str, Any]
    assets: Any


class BasePlugin(ABC):
    """Root plugin abstraction."""

    plugin_kind: str = "generic"

    def __init__(self, metadata: PluginMetadata):
        self.metadata = metadata

    @property
    def plugin_id(self) -> str:
        return self.metadata.plugin_id


class EnemyPlugin(BasePlugin, ABC):
    """Enemy plugin contract."""

    plugin_kind = "enemy"

    @abstractmethod
    def base_config(self) -> Dict[str, Any]:
        """Return enemy base configuration."""

    def spawn_weight(self, level: int) -> float:
        """Return weighted spawn chance for this level."""
        return 0.0

    def scale_config(self, level: int) -> Dict[str, Any]:
        """Return level-scaled enemy configuration."""
        config = dict(self.base_config())
        enemy_type = config.get("type", self.plugin_id)
        if enemy_type == "boss":
            config["health"] = int(config.get("health", 400) * (1 + level * 0.35))
            config["speed"] = max(0.9, config.get("speed", 1.2) * (1 + level * 0.02))
            config["coin_value"] = int(config.get("coin_value", 200) * (1 + level * 0.15))
            config["score_value"] = int(
                config.get("score_value", 1500) * (1 + level * 0.15)
            )
        else:
            config["health"] = int(config.get("health", 30) * (1 + level * 0.2))
            config["speed"] = config.get("speed", 2.0) * (1 + level * 0.05)
            config["coin_value"] = int(config.get("coin_value", 10) * (1 + level * 0.1))
            config["score_value"] = int(
                config.get("score_value", 100) * (1 + level * 0.1)
            )
        return config

    def create(self, x: int, y: int, level: int = 1, target=None) -> "Enemy":
        """Create enemy sprite instance."""
        from entities.enemy import Enemy

        return Enemy(x, y, self.scale_config(level), target=target)


class WeaponPlugin(BasePlugin, ABC):
    """Weapon plugin contract."""

    plugin_kind = "weapon"
    trigger_mode: str = "shoot"  # shoot | ability

    @abstractmethod
    def bullet_config(self) -> Dict[str, Any]:
        """Return base bullet configuration."""

    def get_cooldown(self, player: "Player") -> int:
        return max(1, 5 if getattr(player, "rapid_fire", False) else player.fire_rate)

    def create_bullet(
        self, x: int, y: int, speed: float, damage: int, angle: float = 0
    ) -> "Bullet":
        from entities.bullet import Bullet

        config = dict(self.bullet_config())
        config["type"] = self.plugin_id
        config["speed"] = speed
        return Bullet(x, y, config, damage, angle)

    def fire(
        self, player: "Player", bullet_factory: "BulletFactory"
    ) -> List["Bullet"]:
        """Default shoot behavior with optional triple-shot spread."""
        speed = -16
        angles = [0, -15, 15] if getattr(player, "triple_shot", False) else [0]
        bullets: List["Bullet"] = []
        for angle in angles:
            bullet = self.create_bullet(
                player.rect.centerx,
                player.rect.top,
                speed,
                player.damage,
                angle,
            )
            if bullet:
                bullets.append(bullet)
        return bullets

    def activate_ability(self, game: Any, player: "Player") -> bool:
        """Handle active abilities (trigger_mode='ability'). Return True when consumed."""
        return False

class ShopItemPlugin(BasePlugin, ABC):
    """Shop item plugin contract."""

    plugin_kind = "shop_item"
    persistent_upgrade_key: Optional[str] = None

    @abstractmethod
    def definition(self) -> ShopItemDefinition:
        """Return static definition for this shop item."""

    def cost_for_level(self, level: int) -> int:
        return int(self.definition().base_cost * (1.5 ** level))

    def can_purchase(self, context: ShopPurchaseContext) -> Tuple[bool, Optional[str]]:
        return True, None

    @abstractmethod
    def apply_purchase(self, context: ShopPurchaseContext) -> None:
        """Apply the purchased effect to the player/profile."""


class PowerupPlugin(BasePlugin, ABC):
    """Optional power-up plugin contract."""

    plugin_kind = "powerup"


class LevelPlugin(BasePlugin, ABC):
    """Optional level generation plugin contract."""

    plugin_kind = "level"

