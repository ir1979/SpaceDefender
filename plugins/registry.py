"""Global registries and registration API for Space Defender plugins."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, TypeVar

from .base import EnemyPlugin, WeaponPlugin, ShopItemPlugin

T = TypeVar("T")


@dataclass
class EnemyRegistration:
    plugin: EnemyPlugin


@dataclass
class WeaponRegistration:
    plugin: WeaponPlugin


@dataclass
class ShopItemRegistration:
    plugin: ShopItemPlugin


_enemy_plugins: Dict[str, EnemyRegistration] = {}
_weapon_plugins: Dict[str, WeaponRegistration] = {}
_shop_item_plugins: Dict[str, ShopItemRegistration] = {}


def reset_registries() -> None:
    """Reset all registries. Mostly useful for tests."""
    _enemy_plugins.clear()
    _weapon_plugins.clear()
    _shop_item_plugins.clear()


def _register(
    target: Dict[str, T], key: str, value: T, kind: str, replace: bool = False
) -> None:
    if key in target and not replace:
        raise ValueError(f"Duplicate {kind} id '{key}'")
    target[key] = value


def register_enemy(plugin: EnemyPlugin, replace: bool = False) -> None:
    """Register an enemy plugin implementation."""
    _register(
        _enemy_plugins,
        plugin.plugin_id,
        EnemyRegistration(plugin),
        "enemy plugin",
        replace=replace,
    )


def register_weapon(plugin: WeaponPlugin, replace: bool = False) -> None:
    """Register a weapon plugin implementation."""
    _register(
        _weapon_plugins,
        plugin.plugin_id,
        WeaponRegistration(plugin),
        "weapon plugin",
        replace=replace,
    )


def register_shop_item(plugin: ShopItemPlugin, replace: bool = False) -> None:
    """Register a shop item plugin implementation."""
    _register(
        _shop_item_plugins,
        plugin.plugin_id,
        ShopItemRegistration(plugin),
        "shop item plugin",
        replace=replace,
    )


def get_enemy_plugin(plugin_id: str) -> Optional[EnemyPlugin]:
    item = _enemy_plugins.get(plugin_id)
    return item.plugin if item else None


def get_weapon_plugin(plugin_id: str) -> Optional[WeaponPlugin]:
    item = _weapon_plugins.get(plugin_id)
    return item.plugin if item else None


def get_shop_item_plugin(plugin_id: str) -> Optional[ShopItemPlugin]:
    item = _shop_item_plugins.get(plugin_id)
    return item.plugin if item else None


def list_enemy_plugins() -> List[EnemyPlugin]:
    return [registration.plugin for registration in _enemy_plugins.values()]


def list_weapon_plugins() -> List[WeaponPlugin]:
    return [registration.plugin for registration in _weapon_plugins.values()]


def list_shop_item_plugins() -> List[ShopItemPlugin]:
    return [registration.plugin for registration in _shop_item_plugins.values()]


def get_enemy_plugin_ids() -> List[str]:
    return [plugin.plugin_id for plugin in list_enemy_plugins()]


def get_weapon_plugin_ids() -> List[str]:
    return [plugin.plugin_id for plugin in list_weapon_plugins()]


def get_shop_item_plugins() -> List[ShopItemPlugin]:
    """Backward-compatible alias used by runtime and integrations."""
    return list_shop_item_plugins()
