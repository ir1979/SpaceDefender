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
        """Draw HUD elements with consistent margins and spacing."""
        font_medium = self.assets.fonts['medium']
        font_small = self.assets.fonts['small']

        margin = 20
        spacing = 8
        screen_w = game_config.SCREEN_WIDTH
        screen_h = game_config.SCREEN_HEIGHT

        # Health bar (left-top)
        bar_w = min(260, max(180, screen_w // 5))
        bar_h = 30
        bar_x = margin
        bar_y = margin
        self.draw_bar(surface, bar_x, bar_y, bar_w, bar_h, player.health, 
                      player.max_health, color_config.GREEN, "HEALTH")

        # Score (below health bar)
        y = bar_y + bar_h + spacing * 2
        score_text = font_medium.render(f"Score: {player.score}", True, color_config.WHITE)
        surface.blit(score_text, (bar_x, y))

        # Coins (below score)
        y += font_medium.get_height() + spacing
        coins_text = font_medium.render(f"Coins: {player.coins}", True, color_config.YELLOW)
        surface.blit(coins_text, (bar_x, y))

        # Level & Timer (right-top column, aligned to same right margin)
        right_margin = margin
        level_text = font_medium.render(f"Level: {level}", True, color_config.CYAN)
        level_rect = level_text.get_rect(topright=(screen_w - right_margin, bar_y))
        surface.blit(level_text, level_rect)

        timer_y = bar_y + font_medium.get_height() + spacing * 2
        minutes = int(time_remaining // 60)
        seconds = int(time_remaining % 60)
        timer_text = f"Time: {minutes:02d}:{seconds:02d}"
        timer_color = color_config.RED if time_remaining < 30 else color_config.WHITE
        timer_surface = font_medium.render(timer_text, True, timer_color)
        timer_rect = timer_surface.get_rect(topright=(screen_w - right_margin, timer_y))
        surface.blit(timer_surface, timer_rect)

        # Power-up indicators (stacked under timer, right-aligned)
        pu_x_right = screen_w - right_margin
        pu_y = timer_y + font_medium.get_height() + spacing
        if player.has_shield:
            shield_text = font_small.render("SHIELD", True, color_config.CYAN)
            shield_rect = shield_text.get_rect(topright=(pu_x_right, pu_y))
            surface.blit(shield_text, shield_rect)
            pu_y += shield_rect.height + spacing

        if player.rapid_fire:
            rapid_text = font_small.render("RAPID FIRE", True, color_config.ORANGE)
            rapid_rect = rapid_text.get_rect(topright=(pu_x_right, pu_y))
            surface.blit(rapid_text, rapid_rect)
            pu_y += rapid_rect.height + spacing

        if player.triple_shot:
            triple_text = font_small.render("TRIPLE SHOT", True, color_config.PURPLE)
            triple_rect = triple_text.get_rect(topright=(pu_x_right, pu_y))
            surface.blit(triple_text, triple_rect)

        # Controls hint (bottom-left, with margin)
        hint_text = self.assets.fonts['tiny'].render(
            "SPACE: Shoot | P: Pause | ESC: Quit", 
            True, color_config.UI_TEXT)
        hint_rect = hint_text.get_rect(
            bottomleft=(margin, screen_h - margin))
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
