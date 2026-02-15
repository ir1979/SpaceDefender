"""Collision System Module"""
import pygame
from typing import List, Tuple, Callable

class CollisionSystem:
    """Handles all collision detection and resolution"""
    
    @staticmethod
    def check_rect_collision(rect1: pygame.Rect, rect2: pygame.Rect) -> bool:
        """Check rectangular collision"""
        return rect1.colliderect(rect2)
    
    @staticmethod
    def check_circle_collision(pos1: Tuple[float, float], radius1: float,
                              pos2: Tuple[float, float], radius2: float) -> bool:
        """Check circular collision"""
        dx = pos1[0] - pos2[0]
        dy = pos1[1] - pos2[1]
        distance = (dx**2 + dy**2)**0.5
        return distance < radius1 + radius2
    
    @staticmethod
    def check_group_collision(sprite: pygame.sprite.Sprite,
                            group: pygame.sprite.Group) -> List[pygame.sprite.Sprite]:
        """Check collision with sprite group"""
        return pygame.sprite.spritecollide(sprite, group, False)
    
    @staticmethod
    def resolve_collision(obj1, obj2, callback: Callable = None):
        """Resolve collision between two objects"""
        if callback:
            callback(obj1, obj2)
