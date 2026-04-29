"""
Menu System Module
"""

import pygame
import math
from typing import TYPE_CHECKING, List
from config.settings import color_config, game_config
from systems.save_system import SaveSystem
from systems.logger import get_logger

logger = get_logger("space_defender.shop")

if TYPE_CHECKING:
    from systems.asset_manager import AssetManager
    from systems.save_system import PlayerProfile
    from entities.player import Player


class Shop:
    """In-game shop"""

    def __init__(self, assets: "AssetManager", profile: "PlayerProfile" = None):
        self.assets = assets
        self.profile = profile
        self.items = self.create_shop_items()
        self.selected_index = 0
        self.item_rects = []  # Store rectangles for mouse click detection
        self.scroll_offset = 0  # For scrolling in long item lists
        self.max_visible_items = 5  # Show 5 items at a time
        self._sync_profile_state()

    def set_profile(self, profile: "PlayerProfile"):
        """Attach a profile to the shop and restore saved upgrade state."""
        self.profile = profile
        self._sync_profile_state()

    def _sync_profile_state(self):
        """Restore shop levels and costs from the player's saved profile upgrades."""
        if not self.profile:
            return
        profile_drone = self.profile.upgrade_levels.get("drone_level", 0)
        for item in self.items:
            effect = item.get("effect")
            if effect.startswith("drone_"):
                drone_level = int(effect.split("_")[1])
                item["level"] = 1 if profile_drone >= drone_level else 0
                item["cost"] = int(item["base_cost"] * (1.5 ** item["level"]))
            elif effect in getattr(self.profile, "upgrade_levels", {}):
                item["level"] = self.profile.upgrade_levels.get(effect, 0)
                item["cost"] = int(item["base_cost"] * (1.5 ** item["level"]))

    def create_shop_items(self):
        items = [
            # Upgrades
            {
                "name": "Max Health +20",
                "cost": 75,
                "description": "Increase maximum health",
                "effect": "max_health",
                "level": 0,
                "max_level": 999,
                "base_cost": 75,
                "category": "Upgrades",
            },
            {
                "name": "Damage +10",
                "cost": 100,
                "description": "Increase bullet damage",
                "effect": "damage",
                "level": 0,
                "max_level": 999,
                "base_cost": 100,
                "category": "Upgrades",
            },
            {
                "name": "Speed +1",
                "cost": 80,
                "description": "Increase movement speed",
                "effect": "speed",
                "level": 0,
                "max_level": 999,
                "base_cost": 80,
                "category": "Upgrades",
            },
            {
                "name": "Fire Rate +2",
                "cost": 90,
                "description": "Shoot faster",
                "effect": "fire_rate",
                "level": 0,
                "max_level": 999,
                "base_cost": 90,
                "category": "Upgrades",
            },
            {
                "name": "Heal 50 HP",
                "cost": 60,
                "description": "Restore health",
                "effect": "heal",
                "level": 0,
                "max_level": 999,
                "base_cost": 60,
                "category": "Upgrades",
            },
            {
                "name": "🛡️ Shield",
                "cost": 150,
                "description": "Temporary protection from damage",
                "effect": "shield",
                "level": 0,
                "max_level": 10,
                "base_cost": 150,
                "category": "Upgrades",
            },
            {
                "name": "❤️ Extra Life",
                "cost": 200,
                "description": "Get an extra life/respawn",
                "effect": "extra_life",
                "level": 0,
                "max_level": 3,
                "base_cost": 200,
                "category": "Upgrades",
            },
            # Weapon Power-ups
            {
                "name": "⚡ Triple Shot",
                "cost": 120,
                "description": "Fire 3 bullets at once",
                "effect": "triple_shot",
                "level": 0,
                "max_level": 3,
                "base_cost": 120,
                "category": "Weapons",
            },
            {
                "name": "🔫 Rapid Fire Upgrade",
                "cost": 110,
                "description": "Extreme fire rate boost",
                "effect": "rapid_fire",
                "level": 0,
                "max_level": 5,
                "base_cost": 110,
                "category": "Weapons",
            },
            {
                "name": "🎯 Piercing Shots",
                "cost": 130,
                "description": "Bullets penetrate enemies",
                "effect": "piercing",
                "level": 0,
                "max_level": 1,
                "base_cost": 130,
                "category": "Weapons",
            },
            {
                "name": "💣 ATOMIC BOMB",
                "cost": 250,
                "description": "DESTROY ALL ENEMIES ON SCREEN!",
                "effect": "atomic_bomb",
                "level": 0,
                "max_level": 999,
                "base_cost": 250,
                "category": "Weapons",
            },
            {
                "name": "🌪️ Enemy Freeze",
                "cost": 140,
                "description": "Slow down all enemies temporarily",
                "effect": "enemy_freeze",
                "level": 0,
                "max_level": 3,
                "base_cost": 140,
                "category": "Weapons",
            },
            {
                "name": "🌊 Shockwave",
                "cost": 180,
                "description": "Damage all enemies, more damage up close",
                "effect": "shockwave",
                "level": 0,
                "max_level": 999,
                "base_cost": 180,
                "category": "Weapons",
            },
            {
                "name": "⚡ Chain Lightning",
                "cost": 200,
                "description": "Lightning chains between 5 nearest enemies",
                "effect": "chain_lightning",
                "level": 0,
                "max_level": 999,
                "base_cost": 200,
                "category": "Weapons",
            },
            {
                "name": "💫 Time Warp",
                "cost": 160,
                "description": "Slow all enemies to 25% speed for 5s",
                "effect": "time_warp",
                "level": 0,
                "max_level": 3,
                "base_cost": 160,
                "category": "Weapons",
            },
            {
                "name": "🎯 Spread Burst",
                "cost": 220,
                "description": "Fire 12 bullets in a wide fan pattern",
                "effect": "spread_burst",
                "level": 0,
                "max_level": 999,
                "base_cost": 220,
                "category": "Weapons",
            },
            {
                "name": "☄️ Meteor Strike",
                "cost": 300,
                "description": "Massive damage to 3 random enemies",
                "effect": "meteor_strike",
                "level": 0,
                "max_level": 999,
                "base_cost": 300,
                "category": "Weapons",
            },
            # Drone Support
            {
                "name": "Drone Mk I",
                "cost": 160,
                "description": "Level 1 support drone follows and fires with you.",
                "effect": "drone_1",
                "level": 0,
                "max_level": 1,
                "base_cost": 160,
                "category": "Drones",
                "sprite_name": "engine1",
            },
            {
                "name": "Drone Mk II",
                "cost": 210,
                "description": "Improved drone fire rate and damage.",
                "effect": "drone_2",
                "level": 0,
                "max_level": 1,
                "base_cost": 210,
                "category": "Drones",
                "sprite_name": "engine2",
            },
            {
                "name": "Drone Mk III",
                "cost": 260,
                "description": "Level 3 drone with faster targeting.",
                "effect": "drone_3",
                "level": 0,
                "max_level": 1,
                "base_cost": 260,
                "category": "Drones",
                "sprite_name": "engine3",
            },
            {
                "name": "Drone Mk IV",
                "cost": 320,
                "description": "Advanced drone support for tougher waves.",
                "effect": "drone_4",
                "level": 0,
                "max_level": 1,
                "base_cost": 320,
                "category": "Drones",
                "sprite_name": "engine4",
            },
            {
                "name": "Drone Mk V",
                "cost": 400,
                "description": "Top-tier drone support with stronger firepower.",
                "effect": "drone_5",
                "level": 0,
                "max_level": 1,
                "base_cost": 400,
                "category": "Drones",
                "sprite_name": "engine5",
            },
        ]
        category_order = {
            "Drones": 0,
            "Weapons": 1,
            "Upgrades": 2,
        }
        items.sort(key=lambda item: category_order.get(item.get("category"), 3))
        return items

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
        elif event.type == pygame.MOUSEWHEEL:
            max_scroll = max(0, len(self.items) - self.max_visible_items)
            self.scroll_offset = min(
                max_scroll,
                max(0, self.scroll_offset - event.y),
            )
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Handle legacy scroll events for older pygame versions
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

    def _get_item_effect_description(self, item: dict) -> str:
        effect = item.get("effect", "")
        descriptions = {
            "max_health": "Increase ship health and survivability.",
            "damage": "Increase bullet damage for faster kills.",
            "speed": "Move faster to dodge bullets and reposition.",
            "fire_rate": "Shoot more bullets per second.",
            "heal": "Restore health instantly during battle.",
            "triple_shot": "Fire three bullets at once.",
            "rapid_fire": "Greatly improve your fire rate.",
            "piercing": "Bullets pierce enemies and deal extra damage.",
            "shield": "Gain temporary protection from damage.",
            "extra_life": "Gain another chance after taking fatal damage.",
            "atomic_bomb": "Destroy all on-screen enemies instantly.",
            "enemy_freeze": "Slow enemies for a short time.",
            "shockwave": "Damage all enemies with a radial blast.",
            "chain_lightning": "Electrocute multiple nearby enemies.",
            "time_warp": "Slow all enemies for several seconds.",
            "spread_burst": "Fire a wide fan of bullets.",
            "meteor_strike": "Call meteors to strike random enemies.",
        }
        return descriptions.get(effect, item.get("description", "No details available."))

    def draw_item_info_panel(
        self,
        surface: pygame.Surface,
        item: dict,
        x: int,
        y: int,
        width: int,
        height: int,
        player_coins: int,
    ):
        title_surface = self.assets.fonts["medium"].render("Selected Item", True, color_config.CYAN)
        surface.blit(title_surface, (x, y))

        sprite_name = item.get("sprite_name")
        if sprite_name:
            sprite = self.assets.get_sprite(sprite_name)
            if sprite:
                sprite_image = pygame.transform.smoothscale(sprite, (72, 72))
                surface.blit(sprite_image, (x + width - 90, y))

        y += title_surface.get_height() + 12
        description = self._get_item_effect_description(item)
        desc_surface = self.assets.fonts["small"].render(description, True, color_config.WHITE)
        surface.blit(desc_surface, (x, y))

        y += desc_surface.get_height() + 18
        level_surface = self.assets.fonts["small"].render(
            f"Level: {item['level']} / {item['max_level']}", True, color_config.UI_TEXT)
        surface.blit(level_surface, (x, y))

        y += level_surface.get_height() + 12
        if item["level"] >= item["max_level"]:
            cost_text = "MAX LEVEL"
            cost_color = color_config.CYAN
        else:
            cost_text = f"Cost: {item['cost']} coins"
            cost_color = color_config.GREEN if player_coins >= item["cost"] else color_config.RED

        cost_surface = self.assets.fonts["small"].render(cost_text, True, cost_color)
        surface.blit(cost_surface, (x, y))

        y += cost_surface.get_height() + 12
        effect_surface = self.assets.fonts["small"].render(
            f"Effect: {item['description']}", True, color_config.UI_TEXT)
        surface.blit(effect_surface, (x, y))

        progress_label = self.assets.fonts["tiny"].render(
            f"Upgrade Progress: {item['level']} / {item['max_level']}", True, color_config.UI_TEXT)
        progress_rect = pygame.Rect(x, y + effect_surface.get_height() + 12, width - 32, 18)
        pygame.draw.rect(surface, (*color_config.UI_BORDER, 120), progress_rect, border_radius=8)
        if item['max_level'] > 0:
            progress_fill = int((width - 36) * (item['level'] / item['max_level']))
            pygame.draw.rect(surface, (*color_config.CYAN, 180), (x + 2, y + effect_surface.get_height() + 14, progress_fill, 14), border_radius=8)
        surface.blit(progress_label, (x, y + effect_surface.get_height() + 10))

        y += effect_surface.get_height() + progress_label.get_height() + 22
        action_text = "Affordable" if player_coins >= item["cost"] else "Insufficient coins"
        action_color = color_config.GREEN if player_coins >= item["cost"] else color_config.RED
        action_surface = self.assets.fonts["small"].render(action_text, True, action_color)
        surface.blit(action_surface, (x, y))

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
            # Special conditions for certain items
            if item["effect"] == "heal" and player.health >= player.max_health:
                logger.warning(
                    f"✗ Purchase denied: {item['name']} - already at max health"
                )
                self._safe_play_sound(
                    "menu_select", 0.7
                )  # Use existing sound instead of missing 'error'
                return

            if (
                item["effect"] == "shield"
                and hasattr(player, "has_shield")
                and player.has_shield
            ):
                logger.warning(
                    f"✗ Purchase denied: {item['name']} - already have shield"
                )
                self._safe_play_sound(
                    "menu_select", 0.7
                )  # Use existing sound instead of missing 'error'
                return

            logger.info(f"✓ Purchase approved: {item['name']} for {item['cost']} coins")
            if profile is not None and hasattr(profile, "apply_purchase"):
                # Keep profile and profile credit in sync when a profile is active.
                # Only refresh profile coins upward from the session balance, but do
                # not overwrite profile credit when the profile has a larger balance.
                if player.coins > int(profile.coins):
                    profile.coins = player.coins
                if not profile.apply_purchase(item["cost"]):
                    logger.warning(
                        f"✗ Purchase denied: {item['name']} - insufficient profile coins"
                    )
                    self._safe_play_sound("menu_select", 0.7)
                    return
                player.coins = int(profile.coins)
            else:
                player.coins -= item["cost"]
            self._safe_play_sound("shop_purchase", 0.7)

            # Core Upgrades
            if item["effect"] == "max_health":
                player.max_health += 20
                player.health = player.max_health
                logger.info(
                    f"  -> Max Health increased to {player.max_health}, Health restored to {player.health}"
                )
            elif item["effect"] == "damage":
                player.damage += 10
                logger.info(f"  -> Damage increased to {player.damage}")
            elif item["effect"] == "speed":
                player.speed = min(player.speed + 1, 12)
                logger.info(f"  -> Speed increased to {player.speed}")
            elif item["effect"] == "fire_rate":
                player.fire_rate = max(player.fire_rate - 2, 3)
                logger.info(f"  -> Fire Rate improved to {player.fire_rate}")
            elif item["effect"] == "heal":
                old_health = player.health
                player.health = min(player.health + 50, player.max_health)
                logger.info(f"  -> Health restored: {old_health} -> {player.health}")

            # Weapon Power-ups
            elif item["effect"] == "triple_shot":
                if not hasattr(player, "triple_shot"):
                    player.triple_shot = False
                player.triple_shot = True
                # Increase duration based on level
                if not hasattr(player, "triple_shot_duration"):
                    player.triple_shot_duration = 0
                player.triple_shot_duration = 300 + (item["level"] * 100)  # Frames
                logger.info(
                    f"  -> Triple Shot activated! Duration: {player.triple_shot_duration} frames"
                )

            elif item["effect"] == "rapid_fire":
                # Extreme fire rate boost - reduce fire rate significantly
                player.fire_rate = max(player.fire_rate - 5, 1)
                logger.info(
                    f"  -> RAPID FIRE! Fire Rate improved to {player.fire_rate}"
                )

            elif item["effect"] == "piercing":
                if not hasattr(player, "piercing_shots"):
                    player.piercing_shots = False
                player.piercing_shots = True
                logger.info(f"  -> Piercing Shots enabled! Bullets penetrate enemies")

            # Defense Power-ups
            elif item["effect"] == "shield":
                player.has_shield = True
                logger.info(f"  -> Shield activated!")

            elif item["effect"] == "extra_life":
                if not hasattr(player, "lives"):
                    player.lives = 1
                player.lives += 1
                logger.info(f"  -> Extra life granted! Total lives: {player.lives}")

            elif item["effect"].startswith("drone_"):
                selected_level = int(item["effect"].split("_")[1])
                if getattr(player, "drone_level", 0) >= selected_level:
                    logger.warning(
                        f"✗ Purchase denied: {item['name']} - drone level already unlocked"
                    )
                    self._safe_play_sound("menu_select", 0.7)
                    return
                player.set_drone_level(selected_level)
                if hasattr(player, "current_profile") and player.current_profile:
                    player.current_profile.upgrade_levels["drone_level"] = selected_level
                elif hasattr(player, "profile") and player.profile:
                    player.profile.upgrade_levels["drone_level"] = selected_level
                logger.info(f"  -> Drone Mk {selected_level} unlocked!")

            # Special Abilities
            elif item["effect"] == "atomic_bomb":
                # Add atomic bomb to player's weapons inventory
                player.add_weapon("atomic_bomb")
                # Also add to the current profile for persistence
                if hasattr(player, "current_profile") and player.current_profile:
                    player.current_profile.add_weapon("atomic_bomb")
                    logger.info(
                        f"  -> 💣 ATOMIC BOMB added to profile! Total: {player.current_profile.get_weapon_count('atomic_bomb')}"
                    )
                elif hasattr(player, "profile") and player.profile:
                    player.profile.add_weapon("atomic_bomb")
                    logger.info(
                        f"  -> 💣 ATOMIC BOMB added to profile! Total: {player.profile.get_weapon_count('atomic_bomb')}"
                    )
                logger.info(
                    f"  -> 💣 ATOMIC BOMB added to player! Total in inventory: {player.get_weapon_count('atomic_bomb')}"
                )

            elif item["effect"] == "enemy_freeze":
                # Add enemy freeze to player's weapons inventory
                player.add_weapon("enemy_freeze")
                # Also add to the current profile for persistence
                if hasattr(player, "current_profile") and player.current_profile:
                    player.current_profile.add_weapon("enemy_freeze")
                    logger.info(
                        f"  -> 🌪️ ENEMY FREEZE added to profile! Total: {player.current_profile.get_weapon_count('enemy_freeze')}"
                    )
                elif hasattr(player, "profile") and player.profile:
                    player.profile.add_weapon("enemy_freeze")
                    logger.info(
                        f"  -> 🌪️ ENEMY FREEZE added to profile! Total: {player.profile.get_weapon_count('enemy_freeze')}"
                    )
                player.enemy_freeze_duration = 180 + (item["level"] * 60)  # Frames
                logger.info(
                    f"  -> Enemy Freeze available! Duration: {player.enemy_freeze_duration} frames"
                )

            elif item["effect"] == "shockwave":
                player.add_weapon("shockwave")
                if hasattr(player, "current_profile") and player.current_profile:
                    player.current_profile.add_weapon("shockwave")
                elif hasattr(player, "profile") and player.profile:
                    player.profile.add_weapon("shockwave")
                logger.info(f"  -> 🌊 SHOCKWAVE added to player inventory")

            elif item["effect"] == "chain_lightning":
                player.add_weapon("chain_lightning")
                if hasattr(player, "current_profile") and player.current_profile:
                    player.current_profile.add_weapon("chain_lightning")
                elif hasattr(player, "profile") and player.profile:
                    player.profile.add_weapon("chain_lightning")
                logger.info(f"  -> ⚡ CHAIN LIGHTNING added to player inventory")

            elif item["effect"] == "time_warp":
                player.add_weapon("time_warp")
                if hasattr(player, "current_profile") and player.current_profile:
                    player.current_profile.add_weapon("time_warp")
                elif hasattr(player, "profile") and player.profile:
                    player.profile.add_weapon("time_warp")
                logger.info(f"  -> 💫 TIME WARP added to player inventory")

            elif item["effect"] == "spread_burst":
                player.add_weapon("spread_burst")
                if hasattr(player, "current_profile") and player.current_profile:
                    player.current_profile.add_weapon("spread_burst")
                elif hasattr(player, "profile") and player.profile:
                    player.profile.add_weapon("spread_burst")
                logger.info(f"  -> 🎯 SPREAD BURST added to player inventory")

            elif item["effect"] == "meteor_strike":
                player.add_weapon("meteor_strike")
                if hasattr(player, "current_profile") and player.current_profile:
                    player.current_profile.add_weapon("meteor_strike")
                elif hasattr(player, "profile") and player.profile:
                    player.profile.add_weapon("meteor_strike")
                logger.info(f"  -> ☄️ METEOR STRIKE added to player inventory")

            if profile is not None and item["effect"] in {
                "max_health",
                "damage",
                "speed",
                "fire_rate",
                "extra_life",
                "piercing",
            }:
                profile.upgrade_levels[item["effect"]] = (
                    profile.upgrade_levels.get(item["effect"], 0) + 1
                )

            item["level"] += 1
            item["cost"] = int(item["base_cost"] * (1.5 ** item["level"]))
            logger.info(f"  -> Item level: {item['level']}, New cost: {item['cost']}")
            if profile is not None:
                SaveSystem.save_profile(profile)
                logger.info(f"Profile '{profile.name}' saved after shop purchase.")
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

        # Make panel size relative to screen so it always fits
        panel_width = min(900, game_config.SCREEN_WIDTH - 20)
        panel_height = min(int(game_config.SCREEN_HEIGHT * 0.90), game_config.SCREEN_HEIGHT - 20)
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

        subtitle = self.assets.fonts["small"].render(
            "Upgrade your ship and weapons using coins collected in-game.",
            True,
            color_config.UI_TEXT,
        )
        subtitle_rect = subtitle.get_rect(
            center=(game_config.SCREEN_WIDTH // 2, panel_y + 75)
        )
        surface.blit(subtitle, subtitle_rect)

        section_icons = {
            "Drones": "engine1",
            "Weapons": "gun00",
            "Upgrades": "shield1",
        }
        icon_x = panel_x + 30
        icon_y = panel_y + 110
        for category, sprite_name in section_icons.items():
            sprite = self.assets.get_sprite(sprite_name)
            if sprite:
                icon_image = pygame.transform.smoothscale(sprite, (32, 32))
                surface.blit(icon_image, (icon_x, icon_y))
            label = self.assets.fonts["tiny"].render(category, True, color_config.UI_TEXT)
            label_x = icon_x + 38
            surface.blit(label, (label_x, icon_y + 6))
            icon_x = label_x + label.get_width() + 24

        shop_credit = self._get_shop_credit(player)
        coins_text = self.assets.fonts["medium"].render(
            f"Session: {player.coins}", True, color_config.YELLOW
        )
        surface.blit(coins_text, (panel_x + 30, panel_y + 170))

        if shop_credit != player.coins:
            credit_text = self.assets.fonts["small"].render(
                f"Profile credit: {shop_credit}", True, color_config.CYAN
            )
            surface.blit(credit_text, (panel_x + 30, panel_y + 210))
            item_start_y = panel_y + 245
        else:
            credit_text = self.assets.fonts["small"].render(
                "Profile credit is synced", True, color_config.UI_TEXT
            )
            surface.blit(credit_text, (panel_x + 30, panel_y + 210))
            item_start_y = panel_y + 240

        item_list_width = int((panel_width - 60) * 0.62)
        info_panel_width = (panel_width - 60) - item_list_width
        info_panel_x = panel_x + 30 + item_list_width + 20
        info_panel_y = item_start_y
        info_panel_height = panel_height - (info_panel_y - panel_y) - 80

        # Dynamically fit as many items as the available vertical space allows.
        # Each item is 80px tall; add 10px buffer per item for category headers.
        item_area_height = info_panel_height - 10
        self.max_visible_items = max(2, item_area_height // 90)

        # Get mouse position for hover detection
        mouse_pos = pygame.mouse.get_pos()
        self.item_rects = []  # Reset item rectangles

        # Calculate visible items based on scroll offset
        items_content_area_height = (
            info_panel_height - 20
        )
        item_height = 70

        y_offset = item_start_y
        visible_start = self.scroll_offset
        visible_end = min(visible_start + self.max_visible_items, len(self.items))

        current_category = None

        # Draw scrollbar if needed
        if len(self.items) > self.max_visible_items:
            scrollbar_x = panel_x + item_list_width + 36
            scrollbar_y = item_start_y
            scrollbar_height = panel_y + panel_height - 80 - item_start_y

            # Background
            pygame.draw.rect(
                surface,
                color_config.UI_BORDER,
                (scrollbar_x, scrollbar_y, 8, scrollbar_height),
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
                surface, color_config.CYAN, (scrollbar_x, thumb_y, 8, thumb_height)
            )

        # Draw only visible items — clip to the item list area to prevent overflow
        category_icons = {
            "Drones": "engine1",
            "Weapons": "gun00",
            "Upgrades": "shield1",
        }

        items_clip_rect = pygame.Rect(
            panel_x + 28, item_start_y,
            item_list_width + 4, panel_y + panel_height - 80 - item_start_y
        )
        surface.set_clip(items_clip_rect)

        for i in range(visible_start, visible_end):
            item = self.items[i]
            category = item.get("category")
            if category and category != current_category:
                current_category = category
                header_x = panel_x + 30
                icon_sprite = None
                icon_name = category_icons.get(category)
                if icon_name:
                    icon_sprite = self.assets.get_sprite(icon_name)
                if icon_sprite:
                    icon_image = pygame.transform.smoothscale(icon_sprite, (26, 26))
                    icon_rect = icon_image.get_rect(topleft=(header_x, y_offset))
                    surface.blit(icon_image, icon_rect)
                    header_x += icon_rect.width + 8

                header_surface = self.assets.fonts["small"].render(category.upper(), True, color_config.YELLOW)
                surface.blit(header_surface, (header_x, y_offset + 4))
                y_offset += max(header_surface.get_height(), 26) + 8

            selected = i == self.selected_index
            item_rect = pygame.Rect(panel_x + 30, y_offset, item_list_width, 70)
            self.item_rects.append((i, item_rect))  # Store actual index with rect

            # Highlight on hover or selection
            is_hovered = item_rect.collidepoint(mouse_pos)
            self.draw_shop_item(
                surface,
                item,
                panel_x + 30,
                y_offset,
                item_list_width,
                selected or is_hovered,
                shop_credit,
            )
            y_offset += 80

        surface.set_clip(None)  # Remove clipping

        info_panel_rect = pygame.Rect(
            info_panel_x,
            info_panel_y,
            info_panel_width,
            info_panel_height,
        )
        pygame.draw.rect(surface, (*color_config.UI_BG, 220), info_panel_rect, border_radius=16)
        pygame.draw.rect(surface, color_config.CYAN, info_panel_rect, 2, border_radius=16)

        selected_item = None
        if 0 <= self.selected_index < len(self.items):
            selected_item = self.items[self.selected_index]

        if selected_item:
            self.draw_item_info_panel(
                surface,
                selected_item,
                info_panel_x + 16,
                info_panel_y + 16,
                info_panel_width - 32,
                info_panel_height - 32,
                shop_credit,
            )

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
        item_rect = pygame.Rect(x, y, width, 70)
        base_color = color_config.UI_BORDER if selected else color_config.UI_BG
        outline_color = color_config.CYAN if selected else color_config.UI_BORDER
        pygame.draw.rect(surface, base_color, item_rect, border_radius=12)
        pygame.draw.rect(surface, outline_color, item_rect, 2, border_radius=12)

        if selected:
            highlight_rect = pygame.Rect(x + 4, y + 4, width - 8, 62)
            pygame.draw.rect(surface, (*color_config.CYAN, 40), highlight_rect, border_radius=10)

        sprite_name = item.get("sprite_name")
        sprite_width = 0
        if sprite_name:
            sprite = self.assets.get_sprite(sprite_name)
            if sprite:
                sprite_image = pygame.transform.smoothscale(sprite, (48, 48))
                sprite_rect = sprite_image.get_rect(topright=(x + width - 14, y + 10))
                surface.blit(sprite_image, sprite_rect)
                sprite_width = sprite_rect.width + 8

        name_text = f"{item['name']} [Lv {item['level']}/{item['max_level']}]"
        name_surface = self.assets.fonts["medium"].render(
            name_text, True, color_config.WHITE
        )
        surface.blit(name_surface, (x + 16, y + 10))

        desc_surface = self.assets.fonts["small"].render(
            item["description"], True, color_config.UI_TEXT
        )
        surface.blit(desc_surface, (x + 16, y + 40))

        if item["level"] >= item["max_level"]:
            cost_text = "MAX"
            cost_color = color_config.CYAN
        else:
            cost_text = f"{item['cost']} coins"
            cost_color = color_config.GREEN if player_coins >= item["cost"] else color_config.RED

        cost_surface = self.assets.fonts["medium"].render(cost_text, True, cost_color)
        cost_rect = cost_surface.get_rect(right=x + width - 20 - sprite_width, centery=y + 35)

        badge_rect = pygame.Rect(cost_rect.left - 8, cost_rect.top - 5, cost_rect.width + 16, cost_rect.height + 10)
        pygame.draw.rect(surface, color_config.BLACK, badge_rect, border_radius=8)
        pygame.draw.rect(surface, cost_color, badge_rect, 2, border_radius=8)
        surface.blit(cost_surface, cost_rect)
