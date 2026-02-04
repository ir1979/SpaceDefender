"""Entities module"""
from .base_entity import BaseEntity, ShapeRenderer, EntityFactory
from .player import Player
from .enemy import Enemy, EnemyFactory
from .bullet import Bullet, BulletFactory
from .powerup import PowerUp

# Register entities with factory
EntityFactory.register('player', Player)
EntityFactory.register('enemy', Enemy)
EntityFactory.register('bullet', Bullet)
EntityFactory.register('powerup', PowerUp)

__all__ = [
    'BaseEntity', 'ShapeRenderer', 'EntityFactory',
    'Player', 'Enemy', 'EnemyFactory',
    'Bullet', 'BulletFactory',
    'PowerUp'
]
