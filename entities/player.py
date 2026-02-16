"""
Player Entity Module
"""
import pygame
import math
from typing import List, Dict, Any
from .base_entity import BaseEntity, ShapeRenderer
from config.settings import color_config, player_config

class Player(BaseEntity):
    """Player spaceship"""
    
    def __init__(self, x: int, y: int, shape_type: str = "spaceship", 
                 network_controlled: bool = False, headless: bool = False):
        self.shape_type = shape_type
        self.size = (50, 60)
        self.color = color_config.BLUE
        self.network_controlled = network_controlled  # Client receives position from server
        self.headless = headless  # Server mode - update cooldowns only, no input processing
        
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
        
        # State
        self.invincible = False
        self.invincible_timer = 0
        
        super().__init__(x, y)
    
    def _create_image(self):
        """Create player visual"""
        self.image = ShapeRenderer.create_shape(
            self.shape_type, self.size, self.color)
    
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
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += self.speed
        
        # Movement from mouse (only in single player)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        from config.settings import game_config
        
        # Move player towards mouse position (with dead zone to prevent jitter)
        dist_x = mouse_x - self.rect.centerx
        dist_y = mouse_y - self.rect.centery
        distance = math.sqrt(dist_x**2 + dist_y**2)
        
        # Dead zone: ignore very small distances
        MOUSE_DEAD_ZONE = 25
        
        if distance > MOUSE_DEAD_ZONE:
            # Normalize and apply speed
            norm_x = dist_x / distance
            norm_y = dist_y / distance
            dx += norm_x * self.speed
            dy += norm_y * self.speed
        
        # Apply movement
        self.rect.x += dx
        self.rect.y += dy
        
        # Clamp to screen
        self.rect.clamp_ip(pygame.Rect(
            0, 0, game_config.SCREEN_WIDTH, game_config.SCREEN_HEIGHT))
        
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
    
    def _update_invincibility(self):
        """Update invincibility frames"""
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
            if self.invincible_timer == 0:
                self.invincible = False
    
    def shoot(self, weapon_type: str = "default") -> List['Bullet']:
        """Fire weapon"""
        if self.fire_cooldown > 0:
            return []
        
        from .bullet import BulletFactory
        
        bullets = []
        fire_rate_modifier = 5 if self.rapid_fire else self.fire_rate
        self.fire_cooldown = fire_rate_modifier
        
        speed = -10  # Negative = UP
        
        if self.triple_shot:
            bullets.append(BulletFactory.create(
                weapon_type, self.rect.centerx, self.rect.top, 
                speed, self.damage, 0))
            bullets.append(BulletFactory.create(
                weapon_type, self.rect.centerx, self.rect.top,
                speed, self.damage, -15))
            bullets.append(BulletFactory.create(
                weapon_type, self.rect.centerx, self.rect.top,
                speed, self.damage, 15))
        else:
            bullets.append(BulletFactory.create(
                weapon_type, self.rect.centerx, self.rect.top,
                speed, self.damage, 0))
        
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
        elif power_type == "health":
            self.health = min(self.health + 30, self.max_health)
    
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
    
    def draw(self, surface: pygame.Surface):
        """Draw player with effects"""
        if self.invincible and (self.invincible_timer // 5) % 2:
            return
        
        surface.blit(self.image, self.rect)
        
        # Draw shield
        if self.has_shield:
            pygame.draw.circle(surface, color_config.CYAN, 
                             self.rect.center, 40, 2)
    
    def get_data(self) -> Dict[str, Any]:
        """Get player data"""
        data = super().get_data()
        data.update({
            'health': self.health,
            'max_health': self.max_health,
            'coins': self.coins,
            'score': self.score,
            'shape_type': self.shape_type
        })
        return data
