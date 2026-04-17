"""Plugin runtime bootstrapping for the game process."""

from dataclasses import dataclass
from typing import List

from config.settings import game_config
from systems.logger import get_logger

from .loader import load_plugins
from .registry import list_enemy_plugins, list_shop_item_plugins, list_weapon_plugins

logger = get_logger("space_defender.plugins.runtime")


@dataclass
class PluginRuntimeState:
    """Small summary object for observability/debugging."""

    loaded_modules: List[str]
    failed_modules: List[str]

    @property
    def loaded_count(self) -> int:
        return len(self.loaded_modules)

    @property
    def error_count(self) -> int:
        return len(self.failed_modules)


_BOOTSTRAPPED = False
_STATE = PluginRuntimeState(loaded_modules=[], failed_modules=[])


def bootstrap_plugins() -> PluginRuntimeState:
    """Load all plugin modules exactly once per process."""
    global _BOOTSTRAPPED, _STATE

    if _BOOTSTRAPPED:
        return _STATE

    result = load_plugins(game_config.PLUGIN_DIR)
    _STATE = PluginRuntimeState(
        loaded_modules=result.loaded_modules,
        failed_modules=result.failed_modules,
    )
    _BOOTSTRAPPED = True

    logger.info(
        "Plugin bootstrap complete: modules=%s errors=%s enemies=%s weapons=%s shop_items=%s",
        _STATE.loaded_count,
        _STATE.error_count,
        len(list_enemy_plugins()),
        len(list_weapon_plugins()),
        len(list_shop_item_plugins()),
    )
    return _STATE


def reset_plugin_runtime() -> None:
    """Reset bootstrap state (mainly useful in tests)."""
    global _BOOTSTRAPPED, _STATE
    _BOOTSTRAPPED = False
    _STATE = PluginRuntimeState(loaded_modules=[], failed_modules=[])
