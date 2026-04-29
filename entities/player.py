"""
Player Entity Module
"""

import pygame
import math
from typing import List, Dict, Any, TYPE_CHECKING
from .base_entity import BaseEntity, ShapeRenderer
from config.settings import color_config, player_config

if TYPE_CHECKING:
    from .bullet import Bullet


class Player(BaseEntity):
    """Player spaceship"""

    def __init__(
        self,
        x: int,
        y: int,
        shape_type: str = "spaceship",
        network_controlled: bool = False,
        headless: bool = False,
    ):
        self.shape_type = shape_type
        self.size = (50, 60)
        self.color = color_config.BLUE
        self.network_controlled = (
            network_controlled  # Client receives position from server
        )
        self.headless = (
            headless  # Server mode - update cooldowns only, no input processing
        )

        # Stats
        self.speed = player_config.SPEED
        self.health = player_config.HEALTH
        self.max_health = player_config.HEALTH
        self.damage = player_config.DAMAGE
        self.fire_rate = player_config.FIRE_RATE
        self.fire_cooldown = 0
        self.coins = 0
        self.score = 0

        # Power-ups
        self.has_shield = False
        self.shield_timer = 0
        self.rapid_fire = False
        self.rapid_fire_timer = 0
        self.triple_shot = False
        self.triple_shot_timer = 0
        self.triple_shot_duration = 0  # Frames remaining for triple shot
        self.piercing_shots = False  # Bullets penetrate enemies
        self.piercing_timer = 0
        self.speed_boost = False
        self.speed_boost_timer = 0
        self.damage_boost = False
        self.damage_boost_timer = 0
        self.enemy_freeze_duration = 0  # Frames remaining for enemy freeze
        self.drone_level = 0

        # Combo and score streaks
        self.kill_streak = 0
        self.combo_multiplier = 1
        self.combo_timer = 0
        self.max_combo = 1

        # Game state attributes
        self.lives = 1  # Extra lives
        self.current_profile = None  # Reference to profile for persistence
        self.profile = None  # Alias for current_profile (legacy)

        # Weapon/Special ability inventory
        self.weapons = []  # List of available weapons/abilities: 'atomic_bomb', 'enemy_freeze', etc.
        self.weapon_inventory = {}  # Dict mapping weapon names to counts: {'atomic_bomb': 2, 'enemy_freeze': 1}
        self.selected_weapon_index = 0  # Currently selected weapon

        # Movement and physics
        self.velocity = [0.0, 0.0]
        self.acceleration = player_config.ACCELERATION
        self.max_speed = player_config.MAX_SPEED
        self.drag = player_config.DRAG
        self.mouse_follow_factor = player_config.MOUSE_FOLLOW_FACTOR

        # State
        self.invincible = False
        self.invincible_timer = 0

        super().__init__(x, y)

    def _create_image(self):
        """Create player visual"""
        self.image = ShapeRenderer.create_shape(self.shape_type, self.size, self.color)

    def update(self):
        """Update player state"""
        # HEADLESS MODE (Server): Only update timers and cooldowns
        if self.headless:
            if self.fire_cooldown > 0:
                self.fire_cooldown -= 1
            self._update_powerup_timers()
            self._update_invincibility()
            return

        # NETWORK CONTROLLED (Client in multiplayer): Server manages position
        if self.network_controlled:
            if self.fire_cooldown > 0:
                self.fire_cooldown -= 1
            self._update_powerup_timers()
            self._update_invincibility()
            return

        # LOCAL CONTROL (Single player or local client)
        keys = pygame.key.get_pressed()

        # Movement from keyboard (arrow keys AND WASD)
        move_x = 0.0
        move_y = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_x -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_x += 1.0
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move_y -= 1.0
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move_y += 1.0

        # Mouse guidance remains subtle, not direct teleportation.
        mouse_x, mouse_y = pygame.mouse.get_pos()
        from config.settings import game_config

        dist_x = mouse_x - self.rect.centerx
        dist_y = mouse_y - self.rect.centery
        distance = math.hypot(dist_x, dist_y)
        MOUSE_DEAD_ZONE = 25

        if move_x == 0.0 and move_y == 0.0 and distance > MOUSE_DEAD_ZONE:
            norm_x = dist_x / distance
            norm_y = dist_y / distance
            move_x = norm_x * self.mouse_follow_factor
            move_y = norm_y * self.mouse_follow_factor

        speed_multiplier = 1.35 if self.speed_boost else 1.0
        if move_x != 0.0 or move_y != 0.0:
            magnitude = math.hypot(move_x, move_y)
            if magnitude > 0:
                self.velocity[0] = (move_x / magnitude) * self.speed * speed_multiplier
                self.velocity[1] = (move_y / magnitude) * self.speed * speed_multiplier
        else:
            self.velocity[0] = 0.0
            self.velocity[1] = 0.0

        self.rect.x += int(self.velocity[0])
        self.rect.y += int(self.velocity[1])

        # Clamp to screen
        self.rect.clamp_ip(
            pygame.Rect(0, 0, game_config.SCREEN_WIDTH, game_config.SCREEN_HEIGHT)
        )

        # Update cooldowns
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1

        self._update_powerup_timers()
        self._update_invincibility()

    def _update_powerup_timers(self):
        """Update power-up timers"""
        if self.shield_timer > 0:
            self.shield_timer -= 1
            if self.shield_timer == 0:
                self.has_shield = False

        if self.rapid_fire_timer > 0:
            self.rapid_fire_timer -= 1
            if self.rapid_fire_timer == 0:
                self.rapid_fire = False

        if self.triple_shot_timer > 0:
            self.triple_shot_timer -= 1
            if self.triple_shot_timer == 0:
                self.triple_shot = False

        if self.piercing_timer > 0:
            self.piercing_timer -= 1
            if self.piercing_timer == 0:
                self.piercing_shots = False

        if self.speed_boost_timer > 0:
            self.speed_boost_timer -= 1
            if self.speed_boost_timer == 0:
                self.speed_boost = False

        if self.damage_boost_timer > 0:
            self.damage_boost_timer -= 1
            if self.damage_boost_timer == 0:
                self.damage_boost = False

        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer == 0:
                self.reset_combo()

    def _update_invincibility(self):
        """Update invincibility frames"""
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
            if self.invincible_timer == 0:
                self.invincible = False

    def add_kill_combo(self):
        """Increase combo multiplier when enemies are destroyed in quick succession."""
        self.kill_streak += 1
        self.combo_timer = 180  # 6 seconds at 30 FPS
        self.combo_multiplier = min(5, 1 + self.kill_streak // 3)
        self.max_combo = max(self.max_combo, self.combo_multiplier)
        return self.combo_multiplier

    def reset_combo(self):
        """Reset kill streak and combo bonuses."""
        self.kill_streak = 0
        self.combo_multiplier = 1
        self.combo_timer = 0

    def shoot(self, weapon_type: str = "default") -> List["Bullet"]:
        """Fire weapon"""
        if self.fire_cooldown > 0:
            return []

        from .bullet import BulletFactory

        bullets = []
        fire_rate_modifier = 5 if self.rapid_fire else self.fire_rate
        self.fire_cooldown = fire_rate_modifier

        speed = -16  # Negative = UP
        damage = int(self.damage * (1.25 if self.damage_boost else 1.0))
        bullet_config = {
            'piercing': self.piercing_shots,
        }

        if self.triple_shot:
            bullets.append(
                BulletFactory.create(
                    weapon_type, self.rect.centerx, self.rect.top, speed, damage, 0, extra_config=bullet_config
                )
            )
            bullets.append(
                BulletFactory.create(
                    weapon_type,
                    self.rect.centerx,
                    self.rect.top,
                    speed,
                    damage,
                    -15,
                    extra_config=bullet_config,
                )
            )
            bullets.append(
                BulletFactory.create(
                    weapon_type,
                    self.rect.centerx,
                    self.rect.top,
                    speed,
                    damage,
                    15,
                    extra_config=bullet_config,
                )
            )
        else:
            bullets.append(
                BulletFactory.create(
                    weapon_type, self.rect.centerx, self.rect.top, speed, damage, 0, extra_config=bullet_config
                )
            )

        return [b for b in bullets if b is not None]

    def activate_powerup(self, power_type: str):
        """Activate power-up"""
        if power_type == "shield":
            self.has_shield = True
            self.shield_timer = 300
        elif power_type == "rapid_fire":
            self.rapid_fire = True
            self.rapid_fire_timer = 600
        elif power_type == "triple_shot":
            self.triple_shot = True
            self.triple_shot_timer = 450
        elif power_type == "piercing":
            self.piercing_shots = True
            self.piercing_timer = 360
        elif power_type == "speed_boost":
            self.speed_boost = True
            self.speed_boost_timer = 360
        elif power_type == "damage_boost":
            self.damage_boost = True
            self.damage_boost_timer = 360
        elif power_type == "health":
            self.health = min(self.health + 20, self.max_health)

    def take_damage(self, amount: int):
        """Take damage"""
        if self.invincible:
            return

        if self.has_shield:
            self.has_shield = False
            self.shield_timer = 0
        else:
            self.health -= amount
            self.invincible = True
            self.invincible_timer = 60
            self.reset_combo()

    def draw(self, surface: pygame.Surface):
        """Draw player with effects"""
        if self.invincible and (self.invincible_timer // 5) % 2:
            return

        surface.blit(self.image, self.rect)

        # Draw shield using sprite if available, otherwise fallback to outline
        if self.has_shield:
            shield_sprite = None
            if ShapeRenderer.asset_manager:
                shield_sprite = (
                    ShapeRenderer.asset_manager.get_sprite("shield1")
                    or ShapeRenderer.asset_manager.get_sprite("shield")
                )

            if shield_sprite:
                shield_size = int(max(self.rect.width, self.rect.height) * 1.7)
                shield_image = pygame.transform.smoothscale(shield_sprite, (shield_size, shield_size))
                shield_rect = shield_image.get_rect(center=self.rect.center)
                surface.blit(shield_image, shield_rect)
            else:
                pygame.draw.circle(surface, color_config.CYAN, self.rect.center, 40, 2)

    def add_weapon(self, weapon_name: str):
        """Add a weapon/ability to player's inventory"""
        if weapon_name not in self.weapons:
            self.weapons.append(weapon_name)
            if len(self.weapons) == 1:
                self.selected_weapon_index = 0
        # Add to inventory count
        if weapon_name not in self.weapon_inventory:
            self.weapon_inventory[weapon_name] = 0
        self.weapon_inventory[weapon_name] += 1
        return True

    def has_weapon(self, weapon_name: str) -> bool:
        """Check if player has a specific weapon with available count"""
        return (
            weapon_name in self.weapons
            and self.weapon_inventory.get(weapon_name, 0) > 0
        )

    def use_weapon(self, weapon_name: str) -> bool:
        """Use a weapon from inventory. Returns True if successful."""
        if self.has_weapon(weapon_name):
            self.weapon_inventory[weapon_name] -= 1
            if self.weapon_inventory[weapon_name] <= 0:
                self.weapon_inventory[weapon_name] = 0
                # Optionally remove from weapons list if count is 0
                # But keep it so player knows they had it

            # Persist the decrement to the linked profile, if any.
            profile = getattr(self, "current_profile", None) or getattr(self, "profile", None)
            if profile is not None and hasattr(profile, "weapon_inventory"):
                profile.weapon_inventory[weapon_name] = max(
                    0, profile.weapon_inventory.get(weapon_name, 0) - 1
                )
            return True
        return False

    def set_drone_level(self, level: int):
        """Assign the player a support drone level."""
        self.drone_level = max(0, min(5, int(level)))

    def get_weapon_count(self, weapon_name: str) -> int:
        """Get the count of a specific weapon available"""
        return self.weapon_inventory.get(weapon_name, 0)

    def get_selected_weapon(self) -> str:
        """Get the currently selected weapon, or empty string if none"""
        if self.weapons and 0 <= self.selected_weapon_index < len(self.weapons):
            return self.weapons[self.selected_weapon_index]
        return ""

    def select_weapon(self, index: int):
        """Select a weapon by index"""
        if 0 <= index < len(self.weapons):
            self.selected_weapon_index = index

    def cycle_weapon_next(self):
        """Cycle to the next weapon in inventory"""
        if self.weapons:
            self.selected_weapon_index = (self.selected_weapon_index + 1) % len(
                self.weapons
            )

    def cycle_weapon_prev(self):
        """Cycle to the previous weapon in inventory"""
        if self.weapons:
            self.selected_weapon_index = (self.selected_weapon_index - 1) % len(
                self.weapons
            )

    def get_data(self) -> Dict[str, Any]:
        """Get player data"""
        data = super().get_data()
        data.update(
            {
                "health": self.health,
                "max_health": self.max_health,
                "coins": self.coins,
                "score": self.score,
                "shape_type": self.shape_type,
            }
        )
        return data
