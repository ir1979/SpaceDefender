"""Plugin Manager Module"""
import os
import sys
from typing import Dict, List
from .base_plugin import BasePlugin

class PluginManager:
    """Manages game plugins"""
    
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, BasePlugin] = {}
    
    def load_plugin(self, plugin_name: str) -> bool:
        """Load a plugin"""
        try:
            if plugin_name in self.plugins:
                return True
            
            # Import plugin module
            plugin_module = __import__(f"{self.plugin_dir}.{plugin_name}", fromlist=[plugin_name])
            
            # Find plugin class
            for item_name in dir(plugin_module):
                item = getattr(plugin_module, item_name)
                if isinstance(item, type) and issubclass(item, BasePlugin) and item is not BasePlugin:
                    plugin_instance = item()
                    plugin_instance.on_load()
                    self.plugins[plugin_name] = plugin_instance
                    return True
            
            return False
        except Exception as e:
            print(f"Failed to load plugin {plugin_name}: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].on_unload()
            del self.plugins[plugin_name]
            return True
        return False
    
    def get_plugin(self, plugin_name: str) -> BasePlugin:
        """Get a plugin"""
        return self.plugins.get(plugin_name)
    
    def update_all(self):
        """Update all plugins"""
        for plugin in self.plugins.values():
            if plugin.enabled:
                plugin.update()
    
    def get_plugins(self) -> List[BasePlugin]:
        """Get all loaded plugins"""
        return list(self.plugins.values())
