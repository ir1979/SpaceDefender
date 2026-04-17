"""
Menu System Module
"""

import pygame
import math
from typing import TYPE_CHECKING, List
from config.settings import color_config, game_config
from systems.logger import get_logger
from plugins.registry import (
    get_shop_item_plugin,
    list_shop_item_plugins,
    register_shop_item,
)
from plugins.base import ShopPurchaseContext
from plugins.shop.builtins import register_builtin_shop_plugins

logger = get_logger("space_defender.shop")

if TYPE_CHECKING:
    from systems.asset_manager import AssetManager
    from systems.save_system import PlayerProfile
    from entities.player import Player


class Shop:
    """In-game shop"""

    def __init__(self, assets: "AssetManager"):
        self.assets = assets
        register_builtin_shop_plugins(register_shop_item)
        self.items = self.create_shop_items()
        self.selected_index = 0
        self.item_rects = []  # Store rectangles for mouse click detection
        self.scroll_offset = 0  # For scrolling in long item lists
        self.max_visible_items = 5  # Show 5 items at a time

    def create_shop_items(self):
        entries = []
        plugins = sorted(list_shop_item_plugins(), key=lambda p: p.definition().order)
        for plugin in plugins:
            definition = plugin.definition()
            entries.append(
                {
                    "name": definition.name,
                    "cost": definition.base_cost,
                    "description": definition.description,
                    "effect": plugin.plugin_id,
                    "level": 0,
                    "max_level": definition.max_level,
                    "base_cost": definition.base_cost,
                }
            )
        return entries

    def handle_input(self, event: pygame.event.Event, player: "Player") -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Return True to signal the shop should be closed and
                # return to the previous screen (handled in game.py)
                logger.info("Shop closed via ESC key.")
                return True  # Signal to close the shop
            elif event.key == pygame.K_UP or event.key == pygame.K_w:
                self.selected_index = (self.selected_index - 1) % len(self.items)
                self._update_scroll_for_selection()
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.selected_index = (self.selected_index + 1) % len(self.items)
                self._update_scroll_for_selection()
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self.purchase(self.selected_index, player)
        elif event.type == pygame.MOUSEMOTION:
            # Update selection based on mouse hover (only one active at a time)
            for item_index, rect in self.item_rects:
                if rect.collidepoint(event.pos):
                    self.selected_index = item_index
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Handle scroll wheel
            if event.button == 4:  # Scroll up
                self.scroll_offset = max(0, self.scroll_offset - 1)
            elif event.button == 5:  # Scroll down
                max_scroll = max(0, len(self.items) - self.max_visible_items)
                self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
            # Check if mouse clicked on a shop item
            elif event.button == 1:  # Left click
                for item_index, rect in self.item_rects:
                    if rect.collidepoint(event.pos):
                        # Single click selects, second click purchases
                        if self.selected_index == item_index:
                            self.purchase(item_index, player)
                        else:
                            self.selected_index = item_index
                            # play a selection sound for feedback if available
                            try:
                                self._safe_play_sound("menu_select", 0.6)
                            except Exception:
                                pass
                        break
        return False

    def _update_scroll_for_selection(self):
        """Ensure the selected item is visible in the viewport"""
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + self.max_visible_items:
            self.scroll_offset = self.selected_index - self.max_visible_items + 1

    def _safe_play_sound(self, sound_name: str, volume: float = 0.7):
        """Play sound with null safety - gracefully handles missing sounds"""
        try:
            self.assets.play_sound(sound_name, volume)
        except (AttributeError, KeyError):
            pass  # Silently ignore missing sounds

    def _get_shop_credit(self, player: "Player") -> int:
        profile = getattr(player, "current_profile", None) or getattr(player, "profile", None)
        player_coins = getattr(player, "coins", 0)
        if profile and hasattr(profile, "coins"):
            return max(player_coins, int(profile.coins))
        return player_coins

    def purchase(self, index: int, player: "Player"):
        item = self.items[index]
        logger.debug(
            f"Purchase attempt: item='{item['name']}', index={index}, cost={item['cost']}, level={item['level']}, max_level={item['max_level']}"
        )
        logger.debug(
            f"Player coins: {player.coins}, can_afford: {player.coins >= item['cost']}, level_ok: {item['level'] < item['max_level']}"
        )

        profile = getattr(player, "current_profile", None) or getattr(player, "profile", None)
        can_afford_directly = player.coins >= item["cost"]
        can_afford_from_profile = (
            profile is not None
            and hasattr(profile, "apply_purchase")
            and profile.coins >= item["cost"]
        )
        if (can_afford_directly or can_afford_from_profile) and item["level"] < item["max_level"]:
            if not can_afford_directly and can_afford_from_profile:
                profile.apply_purchase(item["cost"])
                player.coins = int(profile.coins)

            plugin = get_shop_item_plugin(item["effect"])
            if plugin is None:
                logger.error(f"No shop plugin registered for effect '{item['effect']}'")
                self._safe_play_sound("menu_select", 0.7)
                return
            context = ShopPurchaseContext(
                shop=self,
                player=player,
                profile=profile,
                item=item,
                assets=self.assets,
            )
            can_purchase, reason = plugin.can_purchase(context)
            if not can_purchase:
                self._safe_play_sound("menu_select", 0.7)
                logger.warning(
                    f"✗ Purchase denied: {item['name']} - {reason or 'conditions not met'}"
                )
                return

            logger.info(f"✓ Purchase approved: {item['name']} for {item['cost']} coins")
            if can_afford_directly:
                player.coins -= item["cost"]
            self._safe_play_sound("shop_purchase", 0.7)

            plugin.apply_purchase(context)
            if profile is not None and plugin.persistent_upgrade_key:
                key = plugin.persistent_upgrade_key
                profile.upgrade_levels[key] = profile.upgrade_levels.get(key, 0) + 1

            item["level"] += 1
            item["cost"] = plugin.cost_for_level(item["level"])
            logger.info(f"  -> Item level: {item['level']}, New cost: {item['cost']}")
        else:
            # Play an error sound for denied purchases
            self._safe_play_sound("menu_select", 0.7)  # Use existing sound
            reason = (
                "insufficient coins"
                if player.coins < item["cost"]
                else (
                    "max level reached"
                    if item["effect"] != "heal"
                    else "already at max health"
                )
            )
            logger.warning(f"✗ Purchase denied: {item['name']} - {reason}")

    def draw(self, surface: pygame.Surface, player: "Player"):
        overlay = pygame.Surface((game_config.SCREEN_WIDTH, game_config.SCREEN_HEIGHT))
        overlay.fill(color_config.BLACK)
        overlay.set_alpha(200)
        surface.blit(overlay, (0, 0))

        panel_width = 700
        panel_height = 600
        panel_x = (game_config.SCREEN_WIDTH - panel_width) // 2
        panel_y = (game_config.SCREEN_HEIGHT - panel_height) // 2

        pygame.draw.rect(
            surface, color_config.UI_BG, (panel_x, panel_y, panel_width, panel_height)
        )
        pygame.draw.rect(
            surface,
            color_config.UI_BORDER,
            (panel_x, panel_y, panel_width, panel_height),
            3,
        )

        title = self.assets.fonts["large"].render("SHOP", True, color_config.CYAN)
        title_rect = title.get_rect(
            center=(game_config.SCREEN_WIDTH // 2, panel_y + 40)
        )
        surface.blit(title, title_rect)

        shop_credit = self._get_shop_credit(player)
        coins_text = self.assets.fonts["medium"].render(
            f"Coins: {player.coins}", True, color_config.YELLOW
        )
        surface.blit(coins_text, (panel_x + 30, panel_y + 90))

        if shop_credit != player.coins:
            credit_text = self.assets.fonts["small"].render(
                f"Profile credit: {shop_credit}", True, color_config.CYAN
            )
            surface.blit(credit_text, (panel_x + 30, panel_y + 120))
            item_start_y = panel_y + 155
        else:
            item_start_y = panel_y + 140

        # Get mouse position for hover detection
        mouse_pos = pygame.mouse.get_pos()
        self.item_rects = []  # Reset item rectangles

        # Calculate visible items based on scroll offset
        items_content_area_height = (
            360  # Space for items (panel_height - title - coins - instructions)
        )
        item_height = 70

        y_offset = item_start_y
        visible_start = self.scroll_offset
        visible_end = min(visible_start + self.max_visible_items, len(self.items))

        # Draw scrollbar if needed
        if len(self.items) > self.max_visible_items:
            scrollbar_x = panel_x + panel_width - 20
            scrollbar_y = panel_y + 140
            scrollbar_height = items_content_area_height

            # Background
            pygame.draw.rect(
                surface,
                color_config.UI_BORDER,
                (scrollbar_x, scrollbar_y, 10, scrollbar_height),
                1,
            )

            # Scrollbar thumb
            thumb_height = max(
                20, int(scrollbar_height * self.max_visible_items / len(self.items))
            )
            thumb_y = scrollbar_y + int(
                (scrollbar_height - thumb_height)
                * self.scroll_offset
                / max(1, len(self.items) - self.max_visible_items)
            )
            pygame.draw.rect(
                surface, color_config.CYAN, (scrollbar_x, thumb_y, 10, thumb_height)
            )

        # Draw only visible items
        for i in range(visible_start, visible_end):
            item = self.items[i]
            selected = i == self.selected_index
            item_rect = pygame.Rect(panel_x + 30, y_offset, panel_width - 70, 70)
            self.item_rects.append((i, item_rect))  # Store actual index with rect

            # Highlight on hover or selection
            is_hovered = item_rect.collidepoint(mouse_pos)
            self.draw_shop_item(
                surface,
                item,
                panel_x + 30,
                y_offset,
                panel_width - 70,
                selected or is_hovered,
                shop_credit,
            )
            y_offset += 80

        instructions = self.assets.fonts["small"].render(
            "↑↓/Scroll: Navigate | Click: Select/Purchase | ESC: Exit",
            True,
            color_config.UI_TEXT,
        )
        instructions_rect = instructions.get_rect(
            center=(game_config.SCREEN_WIDTH // 2, panel_y + panel_height - 30)
        )
        surface.blit(instructions, instructions_rect)

    def draw_shop_item(
        self,
        surface: pygame.Surface,
        item: dict,
        x: int,
        y: int,
        width: int,
        selected: bool,
        player_coins: int,
    ):
        bg_color = color_config.CYAN if selected else color_config.UI_BORDER
        pygame.draw.rect(surface, bg_color, (x, y, width, 70), 2 if not selected else 0)

        if selected:
            pygame.draw.rect(surface, color_config.UI_BG, (x + 3, y + 3, width - 6, 64))

        name_text = f"{item['name']} [Lv {item['level']}/{item['max_level']}]"
        name_surface = self.assets.fonts["medium"].render(
            name_text, True, color_config.WHITE
        )
        surface.blit(name_surface, (x + 10, y + 10))

        desc_surface = self.assets.fonts["small"].render(
            item["description"], True, color_config.UI_TEXT
        )
        surface.blit(desc_surface, (x + 10, y + 40))

        can_afford = player_coins >= item["cost"] and item["level"] < item["max_level"]
        cost_color = color_config.GREEN if can_afford else color_config.RED

        if item["level"] >= item["max_level"]:
            cost_text = "MAX"
        else:
            cost_text = f"{item['cost']} coins"

        cost_surface = self.assets.fonts["medium"].render(cost_text, True, cost_color)
        cost_rect = cost_surface.get_rect(right=x + width - 10, centery=y + 35)
        surface.blit(cost_surface, cost_rect)
