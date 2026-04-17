"""Shop item plugin package."""

from .builtins import register_builtin_shop_plugins
from . import shield_booster  # noqa: F401

__all__ = ["register_builtin_shop_plugins"]

