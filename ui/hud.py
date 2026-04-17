"""
HUD Module
"""
import pygame
import math
from typing import TYPE_CHECKING
from config.settings import color_config, game_config

if TYPE_CHECKING:
    from entities.player import Player
    from systems.asset_manager import AssetManager

class HUD:
    """Heads-Up Display"""
    
    def __init__(self, assets: 'AssetManager'):
        self.assets = assets
        self._weapon_wheel_rotation = 0.0
        self._weapon_wheel_target_rotation = 0.0
        self._last_selected_weapon_index = -1
    
    def draw(self, surface: pygame.Surface, player: 'Player', level: int, 
             time_remaining: float):
        """Draw HUD with compact professional styling and weapon wheel."""
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
        self._draw_panel(surface, bar_x - 8, bar_y - 8, bar_w + 16, bar_h + 16)
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
        info_panel_w = 220
        info_panel_h = 92
        self._draw_panel(
            surface,
            screen_w - right_margin - info_panel_w - 8,
            bar_y - 8,
            info_panel_w + 16,
            info_panel_h + 16,
        )
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

        # Professional weapon wheel at the bottom-center.
        self.draw_weapon_wheel(surface, player)

        # Controls hint (bottom-left, with margin)
        hint_text = self.assets.fonts['tiny'].render(
            "SPACE: Shoot | E: Switch Weapon | B: Use | P: Pause | ESC: Quit", 
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

    def _draw_panel(self, surface: pygame.Surface, x: int, y: int, w: int, h: int):
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (20, 24, 44, 180), (0, 0, w, h), border_radius=12)
        pygame.draw.rect(panel, (*color_config.UI_BORDER, 220), (0, 0, w, h), 2, border_radius=12)
        surface.blit(panel, (x, y))

    def draw_weapon_wheel(self, surface: pygame.Surface, player: 'Player'):
        """Draw semi-circular animated weapon selector."""
        font_small = self.assets.fonts['small']
        font_tiny = self.assets.fonts['tiny']
        screen_w = game_config.SCREEN_WIDTH
        screen_h = game_config.SCREEN_HEIGHT

        panel_w = min(520, screen_w - 80)
        panel_h = 170
        panel_x = (screen_w - panel_w) // 2
        panel_y = screen_h - panel_h - 40
        self._draw_panel(surface, panel_x, panel_y, panel_w, panel_h)

        if not player.weapons:
            text = font_small.render("WEAPON SYSTEM: NONE", True, color_config.UI_TEXT)
            surface.blit(text, text.get_rect(center=(screen_w // 2, panel_y + 84)))
            return

        selected_index = max(0, min(player.selected_weapon_index, len(player.weapons) - 1))
        angle_step = 26
        self._weapon_wheel_target_rotation = -selected_index * angle_step
        self._weapon_wheel_rotation += (
            self._weapon_wheel_target_rotation - self._weapon_wheel_rotation
        ) * 0.2
        self._last_selected_weapon_index = selected_index

        center_x = screen_w // 2
        center_y = panel_y + panel_h + 72
        radius = min(185, panel_w // 2 + 18)
        start_angle = 200

        # Arc baseline
        arc_rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        arc_rect.center = (center_x, center_y)
        pygame.draw.arc(
            surface,
            (80, 120, 180),
            arc_rect,
            math.radians(195),
            math.radians(345),
            2,
        )

        pulse = 0.7 + 0.3 * math.sin(pygame.time.get_ticks() * 0.008)
        for idx, weapon in enumerate(player.weapons):
            angle_deg = start_angle + idx * angle_step + self._weapon_wheel_rotation
            angle = math.radians(angle_deg)
            x = int(center_x + math.cos(angle) * radius)
            y = int(center_y + math.sin(angle) * radius)
            is_selected = idx == selected_index

            base_r = 20 if is_selected else 16
            r = int(base_r * pulse) if is_selected else base_r
            fill = color_config.CYAN if is_selected else color_config.UI_BG
            outline = color_config.WHITE if is_selected else color_config.UI_BORDER
            pygame.draw.circle(surface, fill, (x, y), r)
            pygame.draw.circle(surface, outline, (x, y), r, 2)

            short_name = weapon.replace("_", " ").upper()[:2]
            text = font_tiny.render(short_name, True, color_config.BLACK if is_selected else color_config.WHITE)
            surface.blit(text, text.get_rect(center=(x, y)))

            count = player.get_weapon_count(weapon)
            count_text = font_tiny.render(str(count), True, color_config.YELLOW)
            surface.blit(count_text, count_text.get_rect(center=(x + r - 4, y - r + 6)))

        current_weapon = player.get_selected_weapon()
        display_name = current_weapon.replace("_", " ").upper()
        active_text = font_small.render(
            f"ACTIVE: {display_name} x{player.get_weapon_count(current_weapon)}",
            True,
            color_config.CYAN,
        )
        surface.blit(active_text, active_text.get_rect(center=(center_x, panel_y + 38)))
