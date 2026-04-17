"""Built-in shop item plugins for the default game experience."""

from __future__ import annotations

from typing import Optional, Tuple

from ..base import (
    PluginMetadata,
    ShopItemDefinition,
    ShopItemPlugin,
    ShopPurchaseContext,
)


class BaseBuiltInShopItemPlugin(ShopItemPlugin):
    """Small helper for concise built-in shop plugin declarations."""

    def __init__(
        self,
        plugin_id: str,
        name: str,
        description: str,
        base_cost: int,
        max_level: int = 1,
        order: int = 1000,
        persistent_upgrade_key: Optional[str] = None,
    ):
        super().__init__(
            PluginMetadata(
                plugin_id=plugin_id,
                name=name,
                description=description,
                author="core",
            )
        )
        self._definition = ShopItemDefinition(
            id=plugin_id,
            name=name,
            description=description,
            base_cost=base_cost,
            max_level=max_level,
            order=order,
        )
        self.persistent_upgrade_key = persistent_upgrade_key

    def definition(self) -> ShopItemDefinition:
        return self._definition


class MaxHealthShopItemPlugin(BaseBuiltInShopItemPlugin):
    def __init__(self):
        super().__init__(
            "max_health",
            "Max Health +20",
            "Increase maximum health",
            75,
            max_level=999,
            order=10,
            persistent_upgrade_key="max_health",
        )

    def apply_purchase(self, context: ShopPurchaseContext) -> None:
        context.player.max_health += 20
        context.player.health = context.player.max_health


class DamageShopItemPlugin(BaseBuiltInShopItemPlugin):
    def __init__(self):
        super().__init__(
            "damage",
            "Damage +10",
            "Increase bullet damage",
            100,
            max_level=999,
            order=20,
            persistent_upgrade_key="damage",
        )

    def apply_purchase(self, context: ShopPurchaseContext) -> None:
        context.player.damage += 10


class SpeedShopItemPlugin(BaseBuiltInShopItemPlugin):
    def __init__(self):
        super().__init__(
            "speed",
            "Speed +1",
            "Increase movement speed",
            80,
            max_level=999,
            order=30,
            persistent_upgrade_key="speed",
        )

    def apply_purchase(self, context: ShopPurchaseContext) -> None:
        context.player.speed = min(context.player.speed + 1, 12)


class FireRateShopItemPlugin(BaseBuiltInShopItemPlugin):
    def __init__(self):
        super().__init__(
            "fire_rate",
            "Fire Rate +2",
            "Shoot faster",
            90,
            max_level=999,
            order=40,
            persistent_upgrade_key="fire_rate",
        )

    def apply_purchase(self, context: ShopPurchaseContext) -> None:
        context.player.fire_rate = max(context.player.fire_rate - 2, 3)


class HealShopItemPlugin(BaseBuiltInShopItemPlugin):
    def __init__(self):
        super().__init__(
            "heal",
            "Heal 50 HP",
            "Restore health",
            60,
            max_level=999,
            order=50,
        )

    def can_purchase(self, context: ShopPurchaseContext) -> Tuple[bool, Optional[str]]:
        if context.player.health >= context.player.max_health:
            return False, "already at max health"
        return True, None

    def apply_purchase(self, context: ShopPurchaseContext) -> None:
        context.player.health = min(context.player.health + 50, context.player.max_health)


class TripleShotShopItemPlugin(BaseBuiltInShopItemPlugin):
    def __init__(self):
        super().__init__(
            "triple_shot",
            "⚡ Triple Shot",
            "Fire 3 bullets at once",
            120,
            max_level=3,
            order=60,
        )

    def apply_purchase(self, context: ShopPurchaseContext) -> None:
        player = context.player
        player.triple_shot = True
        duration_frames = 300 + (context.item["level"] * 100)
        player.triple_shot_timer = max(getattr(player, "triple_shot_timer", 0), duration_frames)
        player.triple_shot_duration = player.triple_shot_timer


class RapidFireShopItemPlugin(BaseBuiltInShopItemPlugin):
    def __init__(self):
        super().__init__(
            "rapid_fire",
            "🔫 Rapid Fire Upgrade",
            "Extreme fire rate boost",
            110,
            max_level=5,
            order=70,
        )

    def apply_purchase(self, context: ShopPurchaseContext) -> None:
        context.player.fire_rate = max(context.player.fire_rate - 5, 1)


class PiercingShopItemPlugin(BaseBuiltInShopItemPlugin):
    def __init__(self):
        super().__init__(
            "piercing",
            "🎯 Piercing Shots",
            "Bullets penetrate enemies",
            130,
            max_level=1,
            order=80,
            persistent_upgrade_key="piercing",
        )

    def apply_purchase(self, context: ShopPurchaseContext) -> None:
        context.player.piercing_shots = True


class ShieldShopItemPlugin(BaseBuiltInShopItemPlugin):
    def __init__(self):
        super().__init__(
            "shield",
            "🛡️ Shield",
            "Temporary protection from damage",
            150,
            max_level=10,
            order=90,
        )

    def can_purchase(self, context: ShopPurchaseContext) -> Tuple[bool, Optional[str]]:
        if getattr(context.player, "has_shield", False):
            return False, "already have shield"
        return True, None

    def apply_purchase(self, context: ShopPurchaseContext) -> None:
        context.player.has_shield = True


class ExtraLifeShopItemPlugin(BaseBuiltInShopItemPlugin):
    def __init__(self):
        super().__init__(
            "extra_life",
            "❤️ Extra Life",
            "Get an extra life/respawn",
            200,
            max_level=3,
            order=100,
            persistent_upgrade_key="extra_life",
        )

    def apply_purchase(self, context: ShopPurchaseContext) -> None:
        context.player.lives = getattr(context.player, "lives", 1) + 1


class WeaponUnlockShopItemPlugin(BaseBuiltInShopItemPlugin):
    """Reusable built-in plugin for inventory weapon unlocks."""

    def __init__(
        self,
        plugin_id: str,
        name: str,
        description: str,
        cost: int,
        order: int,
        max_level: int = 999,
    ):
        super().__init__(
            plugin_id=plugin_id,
            name=name,
            description=description,
            base_cost=cost,
            max_level=max_level,
            order=order,
        )
        self.weapon_id = plugin_id

    def apply_purchase(self, context: ShopPurchaseContext) -> None:
        context.player.add_weapon(self.weapon_id)
        if context.profile is not None:
            context.profile.add_weapon(self.weapon_id)


class AtomicBombShopItemPlugin(WeaponUnlockShopItemPlugin):
    def __init__(self):
        super().__init__(
            "atomic_bomb",
            "💣 ATOMIC BOMB",
            "DESTROY ALL ENEMIES ON SCREEN!",
            250,
            110,
        )


class EnemyFreezeShopItemPlugin(WeaponUnlockShopItemPlugin):
    def __init__(self):
        super().__init__(
            "enemy_freeze",
            "🌪️ Enemy Freeze",
            "Slow down all enemies temporarily",
            140,
            120,
            max_level=3,
        )

    def apply_purchase(self, context: ShopPurchaseContext) -> None:
        super().apply_purchase(context)
        context.player.enemy_freeze_duration = 180 + (context.item["level"] * 60)


class ShockwaveShopItemPlugin(WeaponUnlockShopItemPlugin):
    def __init__(self):
        super().__init__(
            "shockwave",
            "🌊 Shockwave",
            "Damage all enemies, more damage up close",
            180,
            130,
        )


class ChainLightningShopItemPlugin(WeaponUnlockShopItemPlugin):
    def __init__(self):
        super().__init__(
            "chain_lightning",
            "⚡ Chain Lightning",
            "Lightning chains between 5 nearest enemies",
            200,
            140,
        )


class TimeWarpShopItemPlugin(WeaponUnlockShopItemPlugin):
    def __init__(self):
        super().__init__(
            "time_warp",
            "💫 Time Warp",
            "Slow all enemies to 25% speed for 5s",
            160,
            150,
            max_level=3,
        )


class SpreadBurstShopItemPlugin(WeaponUnlockShopItemPlugin):
    def __init__(self):
        super().__init__(
            "spread_burst",
            "🎯 Spread Burst",
            "Fire 12 bullets in a wide fan pattern",
            220,
            160,
        )


class MeteorStrikeShopItemPlugin(WeaponUnlockShopItemPlugin):
    def __init__(self):
        super().__init__(
            "meteor_strike",
            "☄️ Meteor Strike",
            "Massive damage to 3 random enemies",
            300,
            170,
        )


def register_builtin_shop_plugins(register_fn=None) -> None:
    """Register built-in shop entries through the given function."""
    if register_fn is None:
        from plugins.registry import register_shop_item as register_fn

    for plugin in [
        MaxHealthShopItemPlugin(),
        DamageShopItemPlugin(),
        SpeedShopItemPlugin(),
        FireRateShopItemPlugin(),
        HealShopItemPlugin(),
        TripleShotShopItemPlugin(),
        RapidFireShopItemPlugin(),
        PiercingShopItemPlugin(),
        ShieldShopItemPlugin(),
        ExtraLifeShopItemPlugin(),
        AtomicBombShopItemPlugin(),
        EnemyFreezeShopItemPlugin(),
        ShockwaveShopItemPlugin(),
        ChainLightningShopItemPlugin(),
        TimeWarpShopItemPlugin(),
        SpreadBurstShopItemPlugin(),
        MeteorStrikeShopItemPlugin(),
    ]:
        register_fn(plugin, replace=True)
