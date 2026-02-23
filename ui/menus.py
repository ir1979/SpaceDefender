"""
Menu System Module
"""
import pygame
import math
from typing import TYPE_CHECKING, List
from config.settings import color_config, game_config
from systems.save_system import SaveSystem
from systems.logger import get_logger

logger = get_logger('space_defender.shop')

if TYPE_CHECKING:
    from systems.asset_manager import AssetManager
    from systems.save_system import PlayerProfile
    from entities.player import Player

class Shop:
    """In-game shop"""
    
    def __init__(self, assets: 'AssetManager'):
        self.assets = assets
        self.items = self.create_shop_items()
        self.selected_index = 0
        self.item_rects = []  # Store rectangles for mouse click detection
        self.scroll_offset = 0  # For scrolling in long item lists
        self.max_visible_items = 5  # Show 5 items at a time
    
    def create_shop_items(self):
        return [
            # Core Upgrades
            {'name': 'Max Health +20', 'cost': 75, 'description': 'Increase maximum health', 
             'effect': 'max_health', 'level': 0, 'max_level': 999, 'base_cost': 75},
            {'name': 'Damage +10', 'cost': 100, 'description': 'Increase bullet damage',
             'effect': 'damage', 'level': 0, 'max_level': 999, 'base_cost': 100},
            {'name': 'Speed +1', 'cost': 80, 'description': 'Increase movement speed',
             'effect': 'speed', 'level': 0, 'max_level': 999, 'base_cost': 80},
            {'name': 'Fire Rate +2', 'cost': 90, 'description': 'Shoot faster',
             'effect': 'fire_rate', 'level': 0, 'max_level': 999, 'base_cost': 90},
            {'name': 'Heal 50 HP', 'cost': 60, 'description': 'Restore health',
             'effect': 'heal', 'level': 0, 'max_level': 999, 'base_cost': 60},
            
            # Weapon Power-ups
            {'name': '⚡ Triple Shot', 'cost': 120, 'description': 'Fire 3 bullets at once',
             'effect': 'triple_shot', 'level': 0, 'max_level': 3, 'base_cost': 120},
            {'name': '🔫 Rapid Fire Upgrade', 'cost': 110, 'description': 'Extreme fire rate boost',
             'effect': 'rapid_fire', 'level': 0, 'max_level': 5, 'base_cost': 110},
            {'name': '🎯 Piercing Shots', 'cost': 130, 'description': 'Bullets penetrate enemies',
             'effect': 'piercing', 'level': 0, 'max_level': 1, 'base_cost': 130},
            
            # Defense Power-ups
            {'name': '🛡️ Shield', 'cost': 150, 'description': 'Temporary protection from damage',
             'effect': 'shield', 'level': 0, 'max_level': 10, 'base_cost': 150},
            {'name': '❤️ Extra Life', 'cost': 200, 'description': 'Get an extra life/respawn',
             'effect': 'extra_life', 'level': 0, 'max_level': 3, 'base_cost': 200},
            
            # Special Abilities
            {'name': '💣 ATOMIC BOMB', 'cost': 250, 'description': 'DESTROY ALL ENEMIES ON SCREEN!',
             'effect': 'atomic_bomb', 'level': 0, 'max_level': 999, 'base_cost': 250},
            {'name': '🌪️ Enemy Freeze', 'cost': 140, 'description': 'Slow down all enemies temporarily',
             'effect': 'enemy_freeze', 'level': 0, 'max_level': 3, 'base_cost': 140},
        ]
    
    def handle_input(self, event: pygame.event.Event, player: 'Player') -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Return True to signal the shop should be closed and
                # return to the previous screen (handled in game.py)
                logger.info("Shop closed via ESC key.")
                return True # Signal to close the shop
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
                                self.assets.play_sound('menu_select', 0.6)
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
    
    def purchase(self, index: int, player: 'Player'):
        item = self.items[index]
        logger.debug(f"Purchase attempt: item='{item['name']}', index={index}, cost={item['cost']}, level={item['level']}, max_level={item['max_level']}")
        logger.debug(f"Player coins: {player.coins}, can_afford: {player.coins >= item['cost']}, level_ok: {item['level'] < item['max_level']}")
        
        if player.coins >= item['cost'] and item['level'] < item['max_level']:
            # Special conditions for certain items
            if item['effect'] == 'heal' and player.health >= player.max_health:
                logger.warning(f"✗ Purchase denied: {item['name']} - already at max health")
                self.assets.play_sound('menu_select', 0.7)  # Use existing sound instead of missing 'error'
                return
            
            if item['effect'] == 'shield' and hasattr(player, 'has_shield') and player.has_shield:
                logger.warning(f"✗ Purchase denied: {item['name']} - already have shield")
                self.assets.play_sound('menu_select', 0.7)  # Use existing sound instead of missing 'error'
                return

            logger.info(f"✓ Purchase approved: {item['name']} for {item['cost']} coins")
            player.coins -= item['cost']
            self.assets.play_sound('shop_purchase', 0.7)
            
            # Core Upgrades
            if item['effect'] == 'max_health':
                player.max_health += 20
                player.health = player.max_health
                logger.info(f"  -> Max Health increased to {player.max_health}, Health restored to {player.health}")
            elif item['effect'] == 'damage':
                player.damage += 10
                logger.info(f"  -> Damage increased to {player.damage}")
            elif item['effect'] == 'speed':
                player.speed = min(player.speed + 1, 12)
                logger.info(f"  -> Speed increased to {player.speed}")
            elif item['effect'] == 'fire_rate':
                player.fire_rate = max(player.fire_rate - 2, 3)
                logger.info(f"  -> Fire Rate improved to {player.fire_rate}")
            elif item['effect'] == 'heal':
                old_health = player.health
                player.health = min(player.health + 50, player.max_health)
                logger.info(f"  -> Health restored: {old_health} -> {player.health}")
            
            # Weapon Power-ups
            elif item['effect'] == 'triple_shot':
                if not hasattr(player, 'triple_shot'):
                    player.triple_shot = False
                player.triple_shot = True
                # Increase duration based on level
                if not hasattr(player, 'triple_shot_duration'):
                    player.triple_shot_duration = 0
                player.triple_shot_duration = 300 + (item['level'] * 100)  # Frames
                logger.info(f"  -> Triple Shot activated! Duration: {player.triple_shot_duration} frames")
            
            elif item['effect'] == 'rapid_fire':
                # Extreme fire rate boost - reduce fire rate significantly
                player.fire_rate = max(player.fire_rate - 5, 1)
                logger.info(f"  -> RAPID FIRE! Fire Rate improved to {player.fire_rate}")
            
            elif item['effect'] == 'piercing':
                if not hasattr(player, 'piercing_shots'):
                    player.piercing_shots = False
                player.piercing_shots = True
                logger.info(f"  -> Piercing Shots enabled! Bullets penetrate enemies")
            
            # Defense Power-ups
            elif item['effect'] == 'shield':
                player.has_shield = True
                logger.info(f"  -> Shield activated!")
            
            elif item['effect'] == 'extra_life':
                if not hasattr(player, 'lives'):
                    player.lives = 1
                player.lives += 1
                logger.info(f"  -> Extra life granted! Total lives: {player.lives}")
            
            # Special Abilities
            elif item['effect'] == 'atomic_bomb':
                # Add atomic bomb to player's weapons inventory
                player.add_weapon('atomic_bomb')
                # Also add to the current profile for persistence
                if hasattr(player, 'current_profile') and player.current_profile:
                    player.current_profile.add_weapon('atomic_bomb')
                    logger.info(f"  -> 💣 ATOMIC BOMB added to profile! Total: {player.current_profile.get_weapon_count('atomic_bomb')}")
                elif hasattr(player, 'profile') and player.profile:
                    player.profile.add_weapon('atomic_bomb')
                    logger.info(f"  -> 💣 ATOMIC BOMB added to profile! Total: {player.profile.get_weapon_count('atomic_bomb')}")
                logger.info(f"  -> 💣 ATOMIC BOMB added to player! Total in inventory: {player.get_weapon_count('atomic_bomb')}")
            
            elif item['effect'] == 'enemy_freeze':
                # Add enemy freeze to player's weapons inventory
                player.add_weapon('enemy_freeze')
                # Also add to the current profile for persistence
                if hasattr(player, 'current_profile') and player.current_profile:
                    player.current_profile.add_weapon('enemy_freeze')
                    logger.info(f"  -> 🌪️ ENEMY FREEZE added to profile! Total: {player.current_profile.get_weapon_count('enemy_freeze')}")
                elif hasattr(player, 'profile') and player.profile:
                    player.profile.add_weapon('enemy_freeze')
                    logger.info(f"  -> 🌪️ ENEMY FREEZE added to profile! Total: {player.profile.get_weapon_count('enemy_freeze')}")
                player.enemy_freeze_duration = 180 + (item['level'] * 60)  # Frames
                logger.info(f"  -> Enemy Freeze available! Duration: {player.enemy_freeze_duration} frames")
            
            item['level'] += 1
            item['cost'] = int(item['base_cost'] * (1.5 ** item['level']))
            logger.info(f"  -> Item level: {item['level']}, New cost: {item['cost']}")
        else:
            # Play an error sound for denied purchases
            self.assets.play_sound('menu_select', 0.7)  # Use existing sound
            reason = "insufficient coins" if player.coins < item['cost'] \
                     else ("max level reached" if item['effect'] != 'heal' else "already at max health")
            logger.warning(f"✗ Purchase denied: {item['name']} - {reason}")

    
    def draw(self, surface: pygame.Surface, player: 'Player'):
        overlay = pygame.Surface((game_config.SCREEN_WIDTH, game_config.SCREEN_HEIGHT))
        overlay.fill(color_config.BLACK)
        overlay.set_alpha(200)
        surface.blit(overlay, (0, 0))
        
        panel_width = 700
        panel_height = 600
        panel_x = (game_config.SCREEN_WIDTH - panel_width) // 2
        panel_y = (game_config.SCREEN_HEIGHT - panel_height) // 2
        
        pygame.draw.rect(surface, color_config.UI_BG, 
                        (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(surface, color_config.UI_BORDER,
                        (panel_x, panel_y, panel_width, panel_height), 3)
        
        title = self.assets.fonts['large'].render("SHOP", True, color_config.CYAN)
        title_rect = title.get_rect(center=(game_config.SCREEN_WIDTH // 2, panel_y + 40))
        surface.blit(title, title_rect)
        
        coins_text = self.assets.fonts['medium'].render(
            f"Coins: {player.coins}", True, color_config.YELLOW)
        surface.blit(coins_text, (panel_x + 30, panel_y + 90))
        
        # Get mouse position for hover detection
        mouse_pos = pygame.mouse.get_pos()
        self.item_rects = []  # Reset item rectangles
        
        # Calculate visible items based on scroll offset
        items_content_area_height = 360  # Space for items (panel_height - title - coins - instructions)
        item_height = 70
        
        y_offset = panel_y + 140
        visible_start = self.scroll_offset
        visible_end = min(visible_start + self.max_visible_items, len(self.items))
        
        # Draw scrollbar if needed
        if len(self.items) > self.max_visible_items:
            scrollbar_x = panel_x + panel_width - 20
            scrollbar_y = panel_y + 140
            scrollbar_height = items_content_area_height
            
            # Background
            pygame.draw.rect(surface, color_config.UI_BORDER,
                           (scrollbar_x, scrollbar_y, 10, scrollbar_height), 1)
            
            # Scrollbar thumb
            thumb_height = max(20, int(scrollbar_height * self.max_visible_items / len(self.items)))
            thumb_y = scrollbar_y + int((scrollbar_height - thumb_height) * self.scroll_offset / max(1, len(self.items) - self.max_visible_items))
            pygame.draw.rect(surface, color_config.CYAN,
                           (scrollbar_x, thumb_y, 10, thumb_height))
        
        # Draw only visible items
        for i in range(visible_start, visible_end):
            item = self.items[i]
            selected = (i == self.selected_index)
            item_rect = pygame.Rect(panel_x + 30, y_offset, panel_width - 70, 70)
            self.item_rects.append((i, item_rect))  # Store actual index with rect
            
            # Highlight on hover or selection
            is_hovered = item_rect.collidepoint(mouse_pos)
            self.draw_shop_item(surface, item, panel_x + 30, y_offset,
                              panel_width - 70, selected or is_hovered, player.coins)
            y_offset += 80
        
        instructions = self.assets.fonts['small'].render(
            "↑↓/Scroll: Navigate | Click: Select/Purchase | ESC: Exit",
            True, color_config.UI_TEXT)
        instructions_rect = instructions.get_rect(
            center=(game_config.SCREEN_WIDTH // 2, panel_y + panel_height - 30))
        surface.blit(instructions, instructions_rect)
    
    def draw_shop_item(self, surface: pygame.Surface, item: dict,
                      x: int, y: int, width: int, selected: bool, player_coins: int):
        bg_color = color_config.CYAN if selected else color_config.UI_BORDER
        pygame.draw.rect(surface, bg_color, (x, y, width, 70), 2 if not selected else 0)
        
        if selected:
            pygame.draw.rect(surface, color_config.UI_BG, (x + 3, y + 3, width - 6, 64))
        
        name_text = f"{item['name']} [Lv {item['level']}/{item['max_level']}]"
        name_surface = self.assets.fonts['medium'].render(name_text, True, color_config.WHITE)
        surface.blit(name_surface, (x + 10, y + 10))
        
        desc_surface = self.assets.fonts['small'].render(
            item['description'], True, color_config.UI_TEXT)
        surface.blit(desc_surface, (x + 10, y + 40))
        
        can_afford = player_coins >= item['cost'] and item['level'] < item['max_level']
        cost_color = color_config.GREEN if can_afford else color_config.RED
        
        if item['level'] >= item['max_level']:
            cost_text = "MAX"
        else:
            cost_text = f"{item['cost']} coins"
        
        cost_surface = self.assets.fonts['medium'].render(cost_text, True, cost_color)
        cost_rect = cost_surface.get_rect(right=x + width - 10, centery=y + 35)
        surface.blit(cost_surface, cost_rect)
