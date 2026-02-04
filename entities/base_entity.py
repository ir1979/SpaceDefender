"""
Base Entity Module
Abstract base classes for all game entities
"""
import pygame
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any

class BaseEntity(pygame.sprite.Sprite, ABC):
    """Abstract base entity class"""
    
    def __init__(self, x: int, y: int):
        super().__init__()
        self.x = x
        self.y = y
        self._create_image()
        self.rect = self.image.get_rect(center=(x, y))
    
    @abstractmethod
    def _create_image(self):
        """Create entity visual representation"""
        pass
    
    @abstractmethod
    def update(self):
        """Update entity state"""
        pass
    
    def get_data(self) -> Dict[str, Any]:
        """Get entity data for serialization"""
        return {
            'type': self.__class__.__name__,
            'x': self.rect.centerx,
            'y': self.rect.centery
        }

class ShapeRenderer:
    """Renders different shapes for entities"""
    
    @staticmethod
    def create_shape(shape_type: str, size: Tuple[int, int], 
                     color: Tuple[int, int, int]) -> pygame.Surface:
        """Create a shape surface"""
        surface = pygame.Surface(size, pygame.SRCALPHA)
        
        if shape_type == "rectangle":
            surface.fill(color)
            pygame.draw.rect(surface, (255, 255, 255), surface.get_rect(), 2)
        
        elif shape_type == "circle":
            radius = min(size) // 2
            center = (size[0] // 2, size[1] // 2)
            pygame.draw.circle(surface, color, center, radius)
            pygame.draw.circle(surface, (255, 255, 255), center, radius, 2)
        
        elif shape_type == "triangle":
            points = [
                (size[0] // 2, 0),
                (size[0], size[1]),
                (0, size[1])
            ]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        elif shape_type == "diamond":
            points = [
                (size[0] // 2, 0),
                (size[0], size[1] // 2),
                (size[0] // 2, size[1]),
                (0, size[1] // 2)
            ]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        elif shape_type == "star":
            center = (size[0] // 2, size[1] // 2)
            outer_radius = min(size) // 2
            inner_radius = outer_radius // 2
            points = []
            
            for i in range(10):
                angle = (i * 36 - 90) * 3.14159 / 180
                radius = outer_radius if i % 2 == 0 else inner_radius
                x = center[0] + radius * pygame.math.Vector2(1, 0).rotate_rad(angle).x
                y = center[1] + radius * pygame.math.Vector2(1, 0).rotate_rad(angle).y
                points.append((x, y))
            
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        else:  # default to rectangle
            surface.fill(color)
        
        return surface

class EntityFactory:
    """Factory for creating entities from configuration"""
    
    _entity_types = {}
    
    @classmethod
    def register(cls, entity_type: str, entity_class):
        """Register an entity type"""
        cls._entity_types[entity_type] = entity_class
    
    @classmethod
    def create(cls, entity_type: str, **kwargs) -> Optional[BaseEntity]:
        """Create an entity instance"""
        entity_class = cls._entity_types.get(entity_type)
        if entity_class:
            return entity_class(**kwargs)
        return None
    
    @classmethod
    def get_registered_types(cls):
        """Get all registered entity types"""
        return list(cls._entity_types.keys())
