"""Base Plugin Module"""
from abc import ABC, abstractmethod

class BasePlugin(ABC):
    """Abstract base plugin class"""
    
    def __init__(self, name: str, version: str = "1.0"):
        self.name = name
        self.version = version
        self.enabled = True
    
    @abstractmethod
    def on_load(self):
        """Called when plugin is loaded"""
        pass
    
    @abstractmethod
    def on_unload(self):
        """Called when plugin is unloaded"""
        pass
    
    @abstractmethod
    def update(self):
        """Called each frame"""
        pass
