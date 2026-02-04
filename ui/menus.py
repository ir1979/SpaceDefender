"""
Menu System Module
"""
import pygame
import math
from typing import TYPE_CHECKING, List
from config.settings import color_config, game_config
from systems.save_system import SaveSystem

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
    
    def create_shop_items(self):
        return [
            {'name': 'Max Health +20', 'cost': 75, 'description': 'Increase maximum health', 
             'effect': 'max_health', 'level': 0, 'max_level': 5, 'base_cost': 75},
            {'name': 'Damage +10', 'cost': 100, 'description': 'Increase bullet damage',
             'effect': 'damage', 'level': 0, 'max_level': 5, 'base_cost': 100},
            {'name': 'Speed +1', 'cost': 80, 'description': 'Increase movement speed',
             'effect': 'speed', 'level': 0, 'max_level': 5, 'base_cost': 80},
            {'name': 'Fire Rate +2', 'cost': 90, 'description': 'Shoot faster',
             'effect': 'fire_rate', 'level': 0, 'max_level': 5, 'base_cost': 90},
            {'name': 'Heal 50 HP', 'cost': 60, 'description': 'Restore health',
             'effect': 'heal', 'level': 0, 'max_level': 999, 'base_cost': 60}
        ]
    
    def handle_input(self, event: pygame.event.Event, player: 'Player') -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_s:
                return True
            elif event.key == pygame.K_UP or event.key == pygame.K_w:
                self.selected_index = (self.selected_index - 1) % len(self.items)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.items)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self.purchase(self.selected_index, player)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Check if mouse clicked on a shop item
            if event.button == 1:  # Left click
                for i, rect in enumerate(self.item_rects):
                    if rect.collidepoint(event.pos):
                        self.selected_index = i
                        self.purchase(i, player)
                        break
        return False
    
    def purchase(self, index: int, player: 'Player'):
        item = self.items[index]
        if player.coins >= item['cost'] and item['level'] < item['max_level']:
            player.coins -= item['cost']
            self.assets.play_sound('shop_purchase', 0.7)
            
            if item['effect'] == 'max_health':
                player.max_health += 20
                player.health = player.max_health
            elif item['effect'] == 'damage':
                player.damage += 10
            elif item['effect'] == 'speed':
                player.speed = min(player.speed + 1, 12)
            elif item['effect'] == 'fire_rate':
                player.fire_rate = max(player.fire_rate - 2, 3)
            elif item['effect'] == 'heal':
                player.health = min(player.health + 50, player.max_health)
            
            item['level'] += 1
            item['cost'] = int(item['base_cost'] * (1.5 ** item['level']))
    
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
        
        y_offset = panel_y + 140
        for i, item in enumerate(self.items):
            selected = (i == self.selected_index)
            item_rect = pygame.Rect(panel_x + 30, y_offset, panel_width - 60, 70)
            self.item_rects.append(item_rect)
            
            # Highlight on hover or selection
            is_hovered = item_rect.collidepoint(mouse_pos)
            self.draw_shop_item(surface, item, panel_x + 30, y_offset,
                              panel_width - 60, selected or is_hovered, player.coins)
            y_offset += 80
        
        instructions = self.assets.fonts['small'].render(
            "Click/↑↓: Navigate | ENTER/Click: Purchase | ESC: Exit",
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
