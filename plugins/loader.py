"""Runtime plugin loader for SpaceDefender."""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass, field
from typing import Dict, List

from systems.logger import get_logger

logger = get_logger("space_defender.plugins.loader")


INFRA_MODULE_NAMES = {
    "base",
    "registry",
    "loader",
    "runtime",
    "base_plugin",
    "plugin_manager",
}


@dataclass
class PluginLoadReport:
    """Result summary for one plugin discovery/import pass."""

    loaded_modules: List[str]
    failed_modules: List[str]
    errors: Dict[str, str] = field(default_factory=dict)


def safe_import_module(module_name: str) -> None:
    """Import a plugin module with a small compatibility wrapper."""
    importlib.import_module(module_name)


class PluginLoader:
    """Discover and import plugin modules under a package."""

    def __init__(self, package_name: str = "plugins"):
        self.package_name = package_name

    def discover_modules(self) -> List[str]:
        """Discover importable plugin modules under the plugin package."""
        try:
            package = importlib.import_module(self.package_name)
        except Exception as exc:
            logger.warning(f"Plugin package '{self.package_name}' not importable: {exc}")
            return []

        package_path = getattr(package, "__path__", None)
        if package_path is None:
            return []

        modules: List[str] = []
        for module_info in pkgutil.walk_packages(package_path, self.package_name + "."):
            module_name = module_info.name
            if module_name.split(".")[-1] in INFRA_MODULE_NAMES:
                continue
            modules.append(module_name)
        return modules

    def load(self) -> PluginLoadReport:
        """Import all discoverable plugins and return a load report."""
        loaded: List[str] = []
        failed: List[str] = []
        errors: Dict[str, str] = {}

        for module_name in self.discover_modules():
            try:
                safe_import_module(module_name)
                loaded.append(module_name)
            except Exception as exc:
                failed.append(module_name)
                errors[module_name] = str(exc)
                logger.error(f"Failed loading plugin module '{module_name}': {exc}")

        logger.info(
            "Plugin loading finished: %d loaded, %d failed",
            len(loaded),
            len(failed),
        )
        return PluginLoadReport(
            loaded_modules=loaded, failed_modules=failed, errors=errors
        )


def discover_plugin_modules(package_name: str = "plugins") -> List[str]:
    """Backward-compatible helper used by older integration code."""
    return PluginLoader(package_name).discover_modules()


def load_plugins(package_name: str = "plugins") -> PluginLoadReport:
    """Backward-compatible helper used by runtime bootstrap."""
    return PluginLoader(package_name).load()
