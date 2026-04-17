"""Weapon plugin package."""

from .builtin_abilities import register_builtin_weapon_abilities
from . import homing_missile  # noqa: F401
from . import homing_missile_unlock  # noqa: F401

__all__ = ["register_builtin_weapon_abilities"]
