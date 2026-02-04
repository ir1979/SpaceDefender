"""
HUD Module
"""
import pygame
from typing import TYPE_CHECKING
from config.settings import color_config, game_config

if TYPE_CHECKING:
    from entities.player import Player
    from systems.asset_manager import AssetManager

class HUD:
    """Heads-Up Display"""
    
    def __init__(self, assets: 'AssetManager'):
        self.assets = assets
    
    def draw(self, surface: pygame.Surface, player: 'Player', level: int, 
             time_remaining: float):
        """Draw HUD elements"""
        font_medium = self.assets.fonts['medium']
        font_small = self.assets.fonts['small']
        
        # Health bar
        self.draw_bar(surface, 20, 20, 200, 30, player.health, 
                     player.max_health, color_config.GREEN, "HEALTH")
        
        # Score
        score_text = font_medium.render(f"Score: {player.score}", True, color_config.WHITE)
        surface.blit(score_text, (20, 60))
        
        # Coins
        coins_text = font_medium.render(f"Coins: {player.coins}", True, color_config.YELLOW)
        surface.blit(coins_text, (20, 100))
        
        # Level
        level_text = font_medium.render(f"Level: {level}", True, color_config.CYAN)
        level_rect = level_text.get_rect(topright=(game_config.SCREEN_WIDTH - 20, 20))
        surface.blit(level_text, level_rect)
        
        # Timer
        minutes = int(time_remaining // 60)
        seconds = int(time_remaining % 60)
        timer_text = f"Time: {minutes:02d}:{seconds:02d}"
        timer_color = color_config.RED if time_remaining < 30 else color_config.WHITE
        timer_surface = font_medium.render(timer_text, True, timer_color)
        timer_rect = timer_surface.get_rect(topright=(game_config.SCREEN_WIDTH - 20, 60))
        surface.blit(timer_surface, timer_rect)
        
        # Power-up indicators
        y_offset = 100
        if player.has_shield:
            shield_text = font_small.render("SHIELD", True, color_config.CYAN)
            surface.blit(shield_text, (game_config.SCREEN_WIDTH - 120, y_offset))
            y_offset += 30
        
        if player.rapid_fire:
            rapid_text = font_small.render("RAPID FIRE", True, color_config.ORANGE)
            surface.blit(rapid_text, (game_config.SCREEN_WIDTH - 150, y_offset))
            y_offset += 30
        
        if player.triple_shot:
            triple_text = font_small.render("TRIPLE SHOT", True, color_config.PURPLE)
            surface.blit(triple_text, (game_config.SCREEN_WIDTH - 150, y_offset))
        
        # Controls hint
        hint_text = self.assets.fonts['tiny'].render(
            "SPACE: Shoot | S: Shop | P: Pause | WASD/Arrows: Move", 
            True, color_config.UI_TEXT)
        hint_rect = hint_text.get_rect(
            bottomleft=(20, game_config.SCREEN_HEIGHT - 10))
        surface.blit(hint_text, hint_rect)
    
    def draw_bar(self, surface: pygame.Surface, x: int, y: int, 
                 width: int, height: int, current: float, maximum: float,
                 color, label: str):
        pygame.draw.rect(surface, color_config.UI_BG, (x, y, width, height))
        pygame.draw.rect(surface, color_config.UI_BORDER, (x, y, width, height), 2)
        
        fill_width = int(width * (current / maximum))
        pygame.draw.rect(surface, color, (x, y, fill_width, height))
        
        label_surface = self.assets.fonts['small'].render(label, True, color_config.WHITE)
        label_rect = label_surface.get_rect(center=(x + width // 2, y + height // 2))
        surface.blit(label_surface, label_rect)
