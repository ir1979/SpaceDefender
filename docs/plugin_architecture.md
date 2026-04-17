# SpaceDefender Plugin & Component Architecture

## 1) Current code summary (modularity-relevant)

The game loop lives in `core/game.py` and directly coordinates enemies, bullets, player state, shop, and profile save/load. Enemy and weapon definitions are currently config-driven (`data/enemies.json`, `data/weapons.json`) through `EnemyFactory` and `BulletFactory`, but behavior hooks are still mostly hardcoded in gameplay flow.

Enemies are spawned from `EnemyFactory.get_random_type()` + `EnemyFactory.create()` and update themselves via movement patterns in `entities/enemy.py`. Weapons projectiles are created by `Player.shoot()` and `BulletFactory.create()`, while several active weapons (atomic bomb, freeze, shockwave, etc.) were historically implemented with explicit `if/elif` branches in the game event loop.

Shop entries were static dictionaries in `ui/menus.py`; purchasing mutated player/profile fields with a large effect switch. Profiles/saves are handled by `systems/save_system.py` with persistent upgrade levels and weapon inventory, then applied back to player state on game startup.

## 2) Proposed plugin-friendly component model

The refactor keeps the existing Pygame sprite model but adds plugin registries and contracts so content can be extended without changing `core/game.py`:

- **Entity-style composition**: sprites remain `pygame.sprite.Sprite`, while behavior/metadata is supplied by plugin objects.
- **Plugin interfaces** (`plugins/base.py`):
  - `EnemyPlugin`: base config, level scaling, spawn weight, enemy creation
  - `WeaponPlugin`: projectile config, fire behavior, cooldown, optional active ability activation
  - `ShopItemPlugin`: item definition + purchase validation/effect
  - optional marker interfaces for future powerup/level plugin types
- **Registries** (`plugins/registry.py`):
  - `register_enemy`, `register_weapon`, `register_shop_item`
  - lookup/list APIs (`get_enemy_plugin`, `list_enemy_plugins`, etc.)
  - duplicate-id protection with optional replace mode
- **Loader/runtime**:
  - `plugins/loader.py` scans and imports plugin modules from `plugins/`
  - `plugins/runtime.py` bootstraps plugin imports once per process
- **Metadata & identity**:
  - `PluginMetadata` and `ShopItemDefinition` provide id/name/description/version/icon, order, max level, cost, etc.
  - plugin IDs are canonical keys; conflicts are avoided by registry uniqueness.

This yields a practical component-based workflow: core systems consume plugin contracts; content modules supply data + behavior.

## 3) Incremental refactor steps (implemented)

1. **Add plugin infrastructure**
   - New: `plugins/base.py`, `plugins/registry.py`, `plugins/loader.py`, `plugins/runtime.py`
   - Export API from `plugins/__init__.py`
2. **Adapt enemy factory to registry**
   - `entities/enemy.py`: wraps config enemies with `ConfigEnemyPlugin`, registers them, and resolves creation via registry.
3. **Adapt weapon factory to registry**
   - `entities/bullet.py`: wraps config weapons with `ConfigWeaponPlugin`, registers them, and resolves projectile creation via registry.
4. **Route player shooting via weapon plugins**
   - `entities/player.py`: `shoot()` first checks `WeaponPlugin`, falling back to legacy behavior.
5. **Move built-in active weapon abilities into plugins**
   - New: `plugins/weapons/builtin_abilities.py`
   - `core/game.py`: ability key now checks plugin `activate_ability()`.
6. **Convert shop entries to shop-item plugins**
   - New: `plugins/shop/builtins.py` with all existing core shop items as `ShopItemPlugin`.
   - `ui/menus.py`: builds item list from shop registry and executes plugin purchase hooks.
7. **Enable runtime discovery**
   - `core/game.py` boots plugin runtime after loading built-in config plugins.
8. **Add extension examples**
   - Enemy plugin, weapon plugin, and shop plugin examples under `plugins/*`.
9. **Add tests + docs**
   - New gameplay plugin registry tests and modder docs.

## 4) Core modules map

- **Base contracts**: `plugins/base.py`
- **Registration and lookups**: `plugins/registry.py`
- **Discovery/import**: `plugins/loader.py`
- **Runtime bootstrap**: `plugins/runtime.py`
- **Built-in shop plugins**: `plugins/shop/builtins.py`
- **Built-in ability weapon plugins**: `plugins/weapons/builtin_abilities.py`
- **Example plugins**:
  - `plugins/enemies/zigzag_bomber.py`
  - `plugins/weapons/homing_missile.py`
  - `plugins/shop/shield_booster.py`
