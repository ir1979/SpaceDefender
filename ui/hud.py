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
    
    def draw(self, surface: pygame.Surface, player: 'Player', level: int, 
             time_remaining: float, time_limit: float = None,
             combo_multiplier: int = 1, wave_number: int = 1):
        """Draw HUD elements with consistent margins and spacing."""
        font_large = self.assets.fonts['large']
        font_medium = self.assets.fonts['medium']
        font_small = self.assets.fonts['small']
        font_tiny = self.assets.fonts['tiny']

        margin = 18
        screen_w = game_config.SCREEN_WIDTH
        screen_h = game_config.SCREEN_HEIGHT

        panel_alpha = 180
        primary_panel_color = (*color_config.UI_BG, panel_alpha)

        # ── Top-left panel: health, score, coins, combo, drone, lives, timer ──
        # Pre-compute content so we can size the panel to fit.
        lh_bar = 32          # health bar height
        lh_gap = 8           # gap after bar
        lh_med = font_medium.get_height() + 4
        lh_sml = font_small.get_height() + 4
        has_drone = getattr(player, 'drone_level', 0) > 0
        has_lives = getattr(player, 'lives', None) is not None

        left_content_h = (lh_bar + lh_gap         # health bar
                          + lh_med                 # score
                          + lh_med                 # coins
                          + lh_sml                 # combo
                          + (lh_sml if has_drone else 0)
                          + (lh_sml if has_lives else 0)
                          + lh_sml)                # timer
        panel_width = max(380, int(screen_w * 0.35))
        panel_height = left_content_h + margin * 2
        panel_x = margin
        panel_y = margin
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(surface, primary_panel_color, panel_rect, border_radius=16)
        pygame.draw.rect(surface, color_config.UI_BORDER, panel_rect, 2, border_radius=16)

        # Health bar
        bar_x = panel_x + 16
        bar_y = panel_y + margin
        bar_w = panel_width - 32
        self.draw_bar(surface, bar_x, bar_y, bar_w, lh_bar,
                      player.health, player.max_health, color_config.GREEN, "HEALTH")

        # Stack remaining items below the bar
        cy = bar_y + lh_bar + lh_gap

        score_text = font_medium.render(f"Score: {player.score}", True, color_config.WHITE)
        surface.blit(score_text, (panel_x + 18, cy))
        cy += lh_med

        coins_text = font_medium.render(f"Coins: {player.coins}", True, color_config.YELLOW)
        surface.blit(coins_text, (panel_x + 18, cy))
        cy += lh_med

        combo_text = font_small.render(
            f"Combo: x{combo_multiplier}", True,
            color_config.ORANGE if combo_multiplier > 1 else color_config.WHITE)
        surface.blit(combo_text, (panel_x + 18, cy))
        cy += lh_sml

        if has_drone:
            drone_text = font_small.render(f"Drone Mk {player.drone_level}", True, color_config.CYAN)
            surface.blit(drone_text, (panel_x + 18, cy))
            cy += lh_sml

        if has_lives:
            lives_text = font_small.render(f"Lives: {player.lives}", True, color_config.CYAN)
            surface.blit(lives_text, (panel_x + 18, cy))
            cy += lh_sml

        time_text = "NO TIME LIMIT"
        if time_remaining is not None:
            time_text = (f"Remaining: {int(time_remaining)}s"
                         if time_limit is not None else
                         f"Elapsed: {int(time_remaining)}s")
        timer_surface = font_small.render(time_text, True, color_config.CYAN)
        surface.blit(timer_surface, (panel_x + 18, cy))

        # ── Top-right panel: level, timer, wave ──
        right_panel_width = max(320, int(screen_w * 0.30))
        rh_large = font_large.get_height() + 6
        rh_med = font_medium.get_height() + 6
        rh_sml = font_small.get_height() + 6
        right_panel_height = margin * 2 + rh_large + rh_med + rh_sml
        right_panel_x = screen_w - right_panel_width - margin
        right_panel_y = margin
        right_panel_rect = pygame.Rect(right_panel_x, right_panel_y, right_panel_width, right_panel_height)
        pygame.draw.rect(surface, primary_panel_color, right_panel_rect, border_radius=16)
        pygame.draw.rect(surface, color_config.UI_BORDER, right_panel_rect, 2, border_radius=16)

        ry = right_panel_y + margin
        level_text = font_large.render(f"LEVEL {level}", True, color_config.CYAN)
        surface.blit(level_text, (right_panel_x + 18, ry))
        ry += rh_large

        timer_label = "REMAINING" if time_limit is not None else "ELAPSED"
        timer_value = time_remaining if time_remaining is not None else 0
        timer_surface = font_medium.render(f"{timer_label}: {int(timer_value)}s", True, color_config.WHITE)
        surface.blit(timer_surface, (right_panel_x + 18, ry))
        ry += rh_med

        wave_surface = font_small.render(f"Wave {wave_number}", True, color_config.CYAN)
        surface.blit(wave_surface, (right_panel_x + 18, ry))

        # Active power-up badges (below right panel)
        powerups = []
        if getattr(player, 'has_shield', False):
            powerups.append(("SHIELD", color_config.CYAN))
        if getattr(player, 'rapid_fire', False):
            powerups.append(("RAPID FIRE", color_config.ORANGE))
        if getattr(player, 'triple_shot', False):
            powerups.append(("TRIPLE SHOT", color_config.PURPLE))
        if getattr(player, 'piercing_shots', False):
            powerups.append(("PIERCE", color_config.YELLOW))
        if getattr(player, 'speed_boost', False):
            powerups.append(("SPEED+", color_config.BLUE))
        if getattr(player, 'damage_boost', False):
            powerups.append(("DAMAGE+", color_config.RED))

        badge_x = right_panel_x + 18
        badge_y = right_panel_y + right_panel_height + 6
        for label, badge_color in powerups:
            badge_surface = font_small.render(label, True, badge_color)
            badge_rect = badge_surface.get_rect(topleft=(badge_x + 8, badge_y + 4))
            badge_bg_width = badge_rect.width + 20
            badge_bg_height = badge_rect.height + 12

            # Wrap to next line if it exceeds screen width
            if badge_x + badge_bg_width > screen_w - margin:
                badge_x = right_panel_x + 18
                badge_y += badge_bg_height + 6

            badge_bg = pygame.Rect(badge_x, badge_y, badge_bg_width, badge_bg_height)
            pygame.draw.rect(surface, (*color_config.BLACK, 200), badge_bg, border_radius=10)
            pygame.draw.rect(surface, badge_color, badge_bg, 2, border_radius=10)
            surface.blit(badge_surface, (badge_x + 12, badge_y + 6))
            badge_x += badge_bg_width + 8

        # ── Bottom-left: circular weapon wheel ──
        weapon_names = {
            'atomic_bomb': 'BOMB',
            'enemy_freeze': 'FREEZE',
            'shield': 'SHIELD',
            'shockwave': 'SHOCK',
            'chain_lightning': 'LIGHT',
            'time_warp': 'WARP',
            'spread_burst': 'SPREAD',
            'meteor_strike': 'METEOR',
        }

        wheel_radius = 100
        wheel_center_x = margin + wheel_radius + 10
        wheel_center_y = screen_h - wheel_radius - margin - 36
        pygame.draw.circle(surface, (*color_config.UI_BG, 220), (wheel_center_x, wheel_center_y), wheel_radius)
        pygame.draw.circle(surface, color_config.UI_BORDER, (wheel_center_x, wheel_center_y), wheel_radius, 3)

        title_surface = font_small.render("WEAPONS", True, color_config.CYAN)
        title_rect = title_surface.get_rect(center=(wheel_center_x, wheel_center_y - 20))
        surface.blit(title_surface, title_rect)

        selected_weapon = player.get_selected_weapon() or "none"
        selected_name = weapon_names.get(selected_weapon, selected_weapon.upper())
        selected_count = player.get_weapon_count(selected_weapon)

        center_text = font_small.render(f"{selected_name}", True, color_config.WHITE)
        center_rect = center_text.get_rect(center=(wheel_center_x, wheel_center_y + 4))
        surface.blit(center_text, center_rect)

        if selected_weapon:
            count_text = font_tiny.render(f"x{selected_count}", True, color_config.YELLOW)
            count_rect = count_text.get_rect(center=(wheel_center_x, wheel_center_y + 26))
            surface.blit(count_text, count_rect)

        if player.weapons:
            num_weapons = len(player.weapons)
            for idx, weapon in enumerate(player.weapons):
                angle = idx * (2 * math.pi / num_weapons) - math.pi / 2
                node_radius = 24
                node_x = wheel_center_x + int(math.cos(angle) * (wheel_radius - 36))
                node_y = wheel_center_y + int(math.sin(angle) * (wheel_radius - 36))
                node_center = (node_x, node_y)
                is_selected = weapon == selected_weapon

                node_color = color_config.CYAN if is_selected else color_config.UI_BORDER
                fill_color = (*color_config.BLACK, 180) if not is_selected else (*color_config.CYAN, 180)
                pygame.draw.circle(surface, fill_color, node_center, node_radius)
                pygame.draw.circle(surface, node_color, node_center, node_radius, 3)

                node_label = weapon_names.get(weapon, weapon[:2].upper())
                label_surface = font_tiny.render(node_label, True, color_config.WHITE)
                label_rect = label_surface.get_rect(center=node_center)
                surface.blit(label_surface, label_rect)

                count_text = font_tiny.render(str(player.get_weapon_count(weapon)), True, color_config.YELLOW)
                count_rect = count_text.get_rect(center=(node_x, node_y + node_radius + 10))
                surface.blit(count_text, count_rect)
        else:
            none_surface = font_small.render("No weapons equipped", True, color_config.UI_TEXT)
            none_rect = none_surface.get_rect(center=(wheel_center_x, wheel_center_y + 40))
            surface.blit(none_surface, none_rect)

        # ── Bottom hint bar: text only, no rectangle ──
        hint_text = font_tiny.render(
            "SPACE: Shoot   E: Switch Weapon   B: Use   P: Pause   ESC: Quit",
            True,
            color_config.UI_TEXT,
        )
        surface.blit(hint_text, (margin + 16, screen_h - margin - hint_text.get_height()))

    def draw_bar(self, surface: pygame.Surface, x: int, y: int, 
                 width: int, height: int, current: float, maximum: float,
                 color, label: str):
        bar_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, color_config.UI_BORDER, bar_rect, 2, border_radius=10)

        fill_ratio = max(0.0, min(1.0, current / maximum))
        fill_width = int(width * fill_ratio)
        pygame.draw.rect(surface, (*color, 180), (x + 1, y + 1, max(0, fill_width - 2), height - 2), border_radius=10)

        label_surface = self.assets.fonts['tiny'].render(label, True, color_config.WHITE)
        label_rect = label_surface.get_rect(center=(x + width // 2, y + height // 2))
        surface.blit(label_surface, label_rect)
