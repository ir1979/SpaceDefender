"""Example enemy plugin: ZigZag Bomber."""

from __future__ import annotations

from typing import Dict

from ..base import EnemyPlugin, PluginMetadata
from ..registry import register_enemy


class ZigZagBomberPlugin(EnemyPlugin):
    """Fast enemy that weaves aggressively and rewards extra score."""

    def __init__(self):
        super().__init__(
            PluginMetadata(
                plugin_id="zigzag_bomber",
                name="ZigZag Bomber",
                description="Fast zigzag attacker with medium durability.",
                author="mod-example",
                version="1.0.0",
            )
        )

    def base_config(self) -> Dict[str, object]:
        return {
            "type": "zigzag_bomber",
            "shape": "enemy_fast",
            "size": [46, 46],
            "color": [255, 90, 40],
            "health": 52,
            "speed": 3.1,
            "movement": "zigzag",
            "coin_value": 24,
            "score_value": 260,
        }

    def spawn_weight(self, level: int) -> float:
        if level < 3:
            return 0.0
        if level < 7:
            return 0.9
        return 1.4


register_enemy(ZigZagBomberPlugin(), replace=True)
