# SpaceDefender Plugin Authoring Guide

This guide explains how to add enemies, weapons, and shop items without touching core gameplay files.

## Folder layout

Put plugin modules under `plugins/`:

- `plugins/enemies/*.py`
- `plugins/weapons/*.py`
- `plugins/shop/*.py`

The loader scans these folders automatically during game startup.

## Core concepts

Use base classes from `plugins.base`:

- `EnemyPlugin`
- `WeaponPlugin`
- `ShopItemPlugin`

Register plugins with:

- `register_enemy(...)`
- `register_weapon(...)`
- `register_shop_item(...)`

from `plugins.registry`.

## Minimal enemy plugin example

```python
from plugins.base import EnemyPlugin, PluginMetadata
from plugins.registry import register_enemy


class HelloEnemy(EnemyPlugin):
    def __init__(self):
        super().__init__(
            PluginMetadata(
                plugin_id="hello_enemy",
                name="Hello Enemy",
                description="A tiny tutorial enemy",
                author="modder",
            )
        )

    def base_config(self):
        return {
            "type": "hello_enemy",
            "shape": "enemy_basic",
            "size": [30, 30],
            "color": [100, 255, 100],
            "health": 20,
            "speed": 2.0,
            "movement": "straight",
            "coin_value": 5,
            "score_value": 60,
        }

    def spawn_weight(self, level: int) -> float:
        return 1.0 if level >= 1 else 0.0


register_enemy(HelloEnemy(), replace=True)
```

## Weapon plugin checklist

1. Subclass `WeaponPlugin`.
2. Set metadata (`plugin_id`, name, description).
3. Implement `bullet_config`.
4. Optionally override:
   - `fire(...)` for projectile patterns
   - `activate_ability(...)` for active ability weapons (`B` key)
   - `get_cooldown(...)`
5. Register using `register_weapon(...)`.

## Shop item plugin checklist

1. Subclass `ShopItemPlugin`.
2. Implement:
   - `definition()` returning `ShopItemDefinition`
   - `apply_purchase(context)`
3. Optionally implement `can_purchase(context)`.
4. Optional persistence:
   - set `persistent_upgrade_key` to update `profile.upgrade_levels`.
5. Register using `register_shop_item(...)`.

## Metadata and IDs

- `plugin_id` must be unique across the relevant plugin category.
- Use lowercase snake_case IDs (`zigzag_bomber`, `shield_booster`).
- Keep names user-facing and descriptions short.

## Assets

You can use existing shape names (`enemy_fast`, `bullet_missile`, etc.) in config.
For custom files, use your own load logic inside plugin code (while staying in pure Python/Pygame).

## Testing plugins

1. Run syntax checks:
   - `python3 -m compileall plugins`
2. Run focused tests:
   - `python3 -m pytest tests/gameplay/test_plugin_registry.py`
3. Start the game and verify:
   - enemy appears in waves
   - weapon functions with shooting/ability key
   - shop item appears and applies effects

## Compatibility guidelines

- Do not mutate global registries outside registration calls.
- Avoid plugin IDs that collide with core IDs unless intentionally overriding (`replace=True`).
- Keep plugin module imports lightweight and side-effect free except registration.
