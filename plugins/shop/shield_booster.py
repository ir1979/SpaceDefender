"""Example shop item plugin: shield booster."""

from __future__ import annotations

from plugins.base import PluginMetadata, ShopItemDefinition, ShopItemPlugin, ShopPurchaseContext
from plugins.registry import register_shop_item


class ShieldBoosterShopItem(ShopItemPlugin):
    """Adds extra shield duration when purchased."""

    def __init__(self):
        super().__init__(
            PluginMetadata(
                plugin_id="shield_booster",
                name="🧪 Shield Booster",
                description="Increase active shield duration and refresh shield",
                author="example-plugin",
            )
        )

    def definition(self) -> ShopItemDefinition:
        return ShopItemDefinition(
            id=self.plugin_id,
            name=self.metadata.name,
            description=self.metadata.description,
            base_cost=175,
            max_level=5,
            order=180,
        )

    def can_purchase(self, context: ShopPurchaseContext):
        if context.player.has_shield and context.player.shield_timer > 900:
            return False, "shield already at high duration"
        return True, None

    def apply_purchase(self, context: ShopPurchaseContext) -> None:
        player = context.player
        player.has_shield = True
        player.shield_timer = max(getattr(player, "shield_timer", 0), 360) + 120


register_shop_item(ShieldBoosterShopItem())
