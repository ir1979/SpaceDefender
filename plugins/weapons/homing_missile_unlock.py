"""Shop item plugin that unlocks homing missile weapon."""

from __future__ import annotations

from plugins.base import PluginMetadata, ShopItemDefinition, ShopItemPlugin, ShopPurchaseContext
from plugins.registry import register_shop_item


class HomingMissileUnlockShopItem(ShopItemPlugin):
    def __init__(self):
        super().__init__(
            PluginMetadata(
                plugin_id="homing_missile_unlock",
                name="🚀 Homing Missiles",
                description="Unlock homing missile launcher weapon",
                author="plugin-example",
            )
        )

    def definition(self) -> ShopItemDefinition:
        return ShopItemDefinition(
            id=self.plugin_id,
            name=self.metadata.name,
            description=self.metadata.description,
            base_cost=260,
            max_level=999,
            order=185,
        )

    def apply_purchase(self, context: ShopPurchaseContext) -> None:
        context.player.add_weapon("homing_missile")
        if context.profile is not None:
            context.profile.add_weapon("homing_missile")


register_shop_item(HomingMissileUnlockShopItem(), replace=True)
