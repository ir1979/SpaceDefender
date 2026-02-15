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
    
    # Optional reference to asset manager for sprite loading
    asset_manager = None
    
    @staticmethod
    def set_asset_manager(asset_mgr):
        """Set the asset manager for sprite loading"""
        ShapeRenderer.asset_manager = asset_mgr
    
    @staticmethod
    def create_shape(shape_type: str, size: Tuple[int, int], 
                     color: Tuple[int, int, int]) -> pygame.Surface:
        """Create a shape surface - tries to load sprite first, falls back to procedural"""
        # Try to load sprite if asset manager is available
        if ShapeRenderer.asset_manager:
            sprite = ShapeRenderer.asset_manager.get_sprite(shape_type)
            if sprite:
                # Scale sprite to desired size and return
                scaled_sprite = pygame.transform.scale(sprite, size)
                return scaled_sprite
        
        # Fall back to procedural shape rendering
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
        
        elif shape_type == "spaceship":
            # Classic spaceship with pointed top
            points = [
                (size[0] // 2, 0),
                (int(size[0] * 0.8), int(size[1] * 0.4)),
                (int(size[0] * 0.6), int(size[1] * 0.5)),
                (size[0], size[1]),
                (size[0] // 2, int(size[1] * 0.7)),
                (0, size[1]),
                (int(size[0] * 0.4), int(size[1] * 0.5)),
                (int(size[0] * 0.2), int(size[1] * 0.4))
            ]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        elif shape_type == "fighter":
            # Sleek fighter jet
            points = [
                (size[0] // 2, 0),
                (int(size[0] * 0.75), int(size[1] * 0.3)),
                (size[0], int(size[1] * 0.4)),
                (int(size[0] * 0.85), int(size[1] * 0.7)),
                (size[0] // 2, int(size[1] * 0.8)),
                (int(size[0] * 0.15), int(size[1] * 0.7)),
                (0, int(size[1] * 0.4)),
                (int(size[0] * 0.25), int(size[1] * 0.3))
            ]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        elif shape_type == "bullet_basic":
            # Standard bullet
            points = [
                (size[0] // 2, 0),
                (size[0], int(size[1] * 0.3)),
                (int(size[0] * 0.8), size[1]),
                (size[0] // 2, int(size[1] * 0.9)),
                (int(size[0] * 0.2), size[1]),
                (0, int(size[1] * 0.3))
            ]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 1)
        
        elif shape_type == "bullet_laser":
            # Thin laser beam
            pygame.draw.line(surface, color, (size[0] // 2, 0), (size[0] // 2, size[1]), 3)
            pygame.draw.circle(surface, (255, 255, 255), (size[0] // 2, 0), 2)
            pygame.draw.circle(surface, (255, 255, 255), (size[0] // 2, size[1]), 2)
        
        elif shape_type == "bullet_plasma":
            # Plasma orb with aura
            center = (size[0] // 2, size[1] // 2)
            radius = min(size) // 2
            pygame.draw.circle(surface, color, center, radius)
            pygame.draw.circle(surface, (255, 255, 255), center, radius, 1)
            pygame.draw.circle(surface, color, center, max(1, radius - 3), 0)
        
        elif shape_type == "bullet_missile":
            # Rocket missile
            points = [
                (int(size[0] * 0.4), 0),
                (int(size[0] * 0.6), 0),
                (int(size[0] * 0.7), int(size[1] * 0.6)),
                (size[0] // 2, size[1]),
                (int(size[0] * 0.3), int(size[1] * 0.6))
            ]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        elif shape_type == "gun_mount":
            # Heavy gun turret
            points = [
                (int(size[0] * 0.3), 0),
                (int(size[0] * 0.7), 0),
                (int(size[0] * 0.8), int(size[1] * 0.4)),
                (int(size[0] * 0.6), int(size[1] * 0.8)),
                (int(size[0] * 0.4), int(size[1] * 0.8)),
                (int(size[0] * 0.2), int(size[1] * 0.4))
            ]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        elif shape_type == "cannon":
            # Heavy cannon barrel
            rect = pygame.Rect(int(size[0] * 0.25), int(size[1] * 0.2), int(size[0] * 0.5), int(size[1] * 0.6))
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, (255, 255, 255), rect, 2)
        
        elif shape_type == "enemy_basic":
            # Simple square enemy with details
            pygame.draw.rect(surface, color, (int(size[0] * 0.2), int(size[1] * 0.2), int(size[0] * 0.6), int(size[1] * 0.6)))
            pygame.draw.rect(surface, (255, 255, 255), (int(size[0] * 0.2), int(size[1] * 0.2), int(size[0] * 0.6), int(size[1] * 0.6)), 2)
            # Eyes
            pygame.draw.circle(surface, (255, 255, 255), (int(size[0] * 0.35), int(size[1] * 0.35)), 2)
            pygame.draw.circle(surface, (255, 255, 255), (int(size[0] * 0.65), int(size[1] * 0.35)), 2)
        
        elif shape_type == "enemy_fast":
            # Sleek fast enemy
            points = [
                (size[0] // 2, 0),
                (size[0], int(size[1] * 0.3)),
                (int(size[0] * 0.8), int(size[1] * 0.7)),
                (size[0], size[1]),
                (size[0] // 2, int(size[1] * 0.8)),
                (0, size[1]),
                (int(size[0] * 0.2), int(size[1] * 0.7)),
                (0, int(size[1] * 0.3))
            ]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        elif shape_type == "enemy_tank":
            # Heavy armored tank
            points = [
                (int(size[0] * 0.1), int(size[1] * 0.3)),
                (int(size[0] * 0.9), int(size[1] * 0.3)),
                (int(size[0] * 0.95), int(size[1] * 0.5)),
                (int(size[0] * 0.95), int(size[1] * 0.8)),
                (size[0] // 2, size[1]),
                (int(size[0] * 0.05), int(size[1] * 0.8)),
                (int(size[0] * 0.05), int(size[1] * 0.5))
            ]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        elif shape_type == "enemy_weaver":
            # Sinuous weaving enemy
            points = [
                (int(size[0] * 0.3), int(size[1] * 0.2)),
                (int(size[0] * 0.7), int(size[1] * 0.2)),
                (int(size[0] * 0.9), int(size[1] * 0.4)),
                (int(size[0] * 0.8), int(size[1] * 0.6)),
                (size[0], int(size[1] * 0.8)),
                (size[0] // 2, size[1]),
                (0, int(size[1] * 0.8)),
                (int(size[0] * 0.2), int(size[1] * 0.6)),
                (int(size[0] * 0.1), int(size[1] * 0.4))
            ]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        elif shape_type == "enemy_boss":
            # Large impressive boss
            center = (size[0] // 2, size[1] // 2)
            # Draw outer circle
            pygame.draw.circle(surface, color, center, min(size) // 2)
            pygame.draw.circle(surface, (255, 255, 255), center, min(size) // 2, 3)
            # Draw inner details
            pygame.draw.circle(surface, (255, 255, 255), center, min(size) // 3, 1)
        
        elif shape_type == "hexagon":
            # Regular hexagon
            center = (size[0] // 2, size[1] // 2)
            radius = min(size) // 2
            points = []
            for i in range(6):
                angle = i * 60 * 3.14159 / 180
                x = center[0] + radius * pygame.math.Vector2(1, 0).rotate_rad(angle).x
                y = center[1] + radius * pygame.math.Vector2(1, 0).rotate_rad(angle).y
                points.append((x, y))
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        elif shape_type == "cross":
            # Plus/cross shape
            pygame.draw.rect(surface, color, (int(size[0] * 0.4), 0, int(size[0] * 0.2), size[1]))
            pygame.draw.rect(surface, color, (0, int(size[1] * 0.4), size[0], int(size[1] * 0.2)))
            pygame.draw.rect(surface, (255, 255, 255), (int(size[0] * 0.4), 0, int(size[0] * 0.2), size[1]), 1)
            pygame.draw.rect(surface, (255, 255, 255), (0, int(size[1] * 0.4), size[0], int(size[1] * 0.2)), 1)
        
        elif shape_type == "crescent":
            # Crescent moon shape
            center = (size[0] // 2, size[1] // 2)
            radius = min(size) // 2
            pygame.draw.circle(surface, color, center, radius)
            # Cut out inner circle for crescent effect
            pygame.draw.circle(surface, (0, 0, 0, 0), (center[0] + radius // 2, center[1]), radius - 3)
            pygame.draw.circle(surface, (255, 255, 255), center, radius, 2)
        
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
