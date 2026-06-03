"""
Main Game Module
"""
import socket
import pygame
import random
import math
import time
from typing import List, Tuple
import os
import sys
# Allow running this file directly (python core/game.py) by adding project
# root to sys.path when executed as a script. Prefer running via `main.py`
# or `python -m core.game` during development.
if __name__ == "__main__" and __package__ is None:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from config.settings import GameState, game_config, color_config
from systems import ParticleSystem, SaveSystem, PlayerProfile, AssetManager
from systems.network import send_data, receive_data, test_connection, DEFAULT_SERVER_HOST, DEFAULT_SERVER_PORT
from systems.logger import get_logger
from entities import Player, EnemyFactory, BulletFactory, PowerUp
from entities.base_entity import ShapeRenderer
from entities.drone import Drone
from ui import HUD, Shop, TextInput

logger = get_logger('space_defender.game')

class Level:
    """Level manager"""
    
    def __init__(self, level_num: int):
        self.level_num = level_num
        self.enemies_to_spawn = 55 + (level_num * 25)
        self.enemies_spawned = 0
        self.boss_spawned = False
        self.spawn_timer = 0
        self.spawn_delay = max(10, 45 - (level_num * 4))
        self.powerup_timer = 0
        self.powerup_delay = max(320, 440 - (level_num * 18))
        self.wave_number = 1
        self.wave_progress = 0
        self.wave_size = max(8, 16 + (level_num * 2))
        self.max_active_enemies = min(26, 14 + level_num * 2)
        self.start_time = time.time()
        self.elapsed_time = 0.0
        self.time_limit = game_config.LEVEL_TIME_LIMIT
        self.time_remaining = float(self.time_limit)
    
    def update_timer(self):
        self.elapsed_time = time.time() - self.start_time
        self.time_remaining = max(0.0, self.time_limit - self.elapsed_time)
        return self.time_remaining > 0.0
    
    def should_spawn_enemy(self, active_enemy_count: int) -> bool:
        if self.enemies_spawned >= self.enemies_to_spawn:
            return False

        if active_enemy_count >= self.max_active_enemies:
            return False

        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_delay:
            self.spawn_timer = 0
            self.enemies_spawned += 1
            self.wave_progress += 1
            if self.wave_progress >= self.wave_size:
                self.wave_progress = 0
                self.wave_number += 1
                self.spawn_delay = max(10, self.spawn_delay - 2)
                self.max_active_enemies = min(24, self.max_active_enemies + 1)
            return True
        return False
    
    def should_spawn_powerup(self) -> bool:
        self.powerup_timer += 1
        if self.powerup_timer >= self.powerup_delay:
            self.powerup_timer = 0
            chance = max(0.05, 0.12 - (self.level_num - 1) * 0.003)
            return random.random() < chance
        return False

    def should_spawn_boss(self, active_regular_enemies: int) -> bool:
        """Spawn one boss once per level after the regular wave has finished."""
        if self.boss_spawned:
            return False
        if self.level_num < 4:
            return False
        if self.enemies_spawned < self.enemies_to_spawn:
            return False
        if active_regular_enemies > 0:
            return False
        self.boss_spawned = True
        return True

class Game:
    """Main game controller"""
    def __init__(self, profile: PlayerProfile = None, is_server=False, fullscreen=False):
        """
        Initializes the Game.
        :param is_server: If True, runs without GUI, Assets, or Sound.
        :param fullscreen: If True, opens the game in fullscreen mode.
        """
        self.is_server = is_server
        self.is_network_mode = False # Default to False, client will set to True
        self.player_id = None # Will be assigned by server during handshake
        self.running = True
        self.fullscreen = fullscreen
        
        # --- 1. Headless vs GUI Environment Setup ---
        if self.is_server:
            # Prevent Pygame from opening a window or initializing audio hardware
            os.environ['SDL_VIDEODRIVER'] = 'dummy'
            os.environ['SDL_AUDIODRIVER'] = 'dummy'
            pygame.init()
            self.screen = None
            self.assets = None  # No images/sounds loaded on server
        else:
            pygame.init()
            if self.fullscreen:
                display_info = pygame.display.Info()
                game_config.SCREEN_WIDTH = display_info.current_w
                game_config.SCREEN_HEIGHT = display_info.current_h
                self.screen = pygame.display.set_mode(
                    (game_config.SCREEN_WIDTH, game_config.SCREEN_HEIGHT),
                    pygame.FULLSCREEN,
                )
            else:
                self.screen = pygame.display.set_mode((game_config.SCREEN_WIDTH, game_config.SCREEN_HEIGHT))
            pygame.display.set_caption(game_config.TITLE)
            self.assets = AssetManager()
        
        self.clock = pygame.time.Clock()

        # --- 2. Universal Logic State (Required by both) ---
        # We set default values even for things the server doesn't "use" 
        # to prevent AttributeErrors during the update() loop.
        self.state = GameState.PLAYING if self.is_server else GameState.SPLASH_SCREEN
        self.current_level = 1
        self.level = None
        self.players: List[Player] = []
        self.player = None  # Local player for client
        
        # Sprite groups are used for collision logic on the server
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.drones = pygame.sprite.Group()

        # --- 3. GUI & Feedback Variables (Always initialized to avoid crashes) ---
        self.duplicate_error_timer = 0
        self.duplicate_profile_error = False
        self.profile = profile
        self.current_profile = profile
        
        # Client-specific UI attributes (initialized for all, but only used on client)
        self.splash_ready = False
        self.splash_loading_timer = 0
        self.splash_timer = 0
        self.splash_skipped = False
        self.loading_progress = 0
        self.loading_items = []
        self.loading_items_total = 0
        self.background_music_playing = False
        self.existing_profiles = []
        self.profile_buttons = []
        self.profile_selected_index = 0
        self.new_profile_button = None  # Button for creating new profile
        self.creating_new_profile = False
        self.menu_buttons = []
        self.menu_selected_index = 0
        self.menu_animation_phase = 0.0
        self.menu_hover_alpha = 80
        self.next_level_pending = False
        self.daily_challenge = None
        self.text_input = None
        self.quit_confirm_selected = True
        self.quit_confirm_hovered = None
        self.quit_confirm_context = 'game'
        self.quit_yes_rect = None
        self.quit_no_rect = None
        self.game_state_from_server = None
        self.server_socket = None
        self.server_host = DEFAULT_SERVER_HOST  # Default server host
        self.server_port = DEFAULT_SERVER_PORT  # Default server port
        
        # Server connection UI variables
        self.server_connect_input = None  # TextInput for server address
        self.server_port_input = None  # TextInput for server port
        self.server_test_button_rect = None  # Button rect for test connection
        self.server_connect_button_rect = None  # Button rect for connect
        self.server_back_button_rect = None  # Button rect for back
        self.server_test_result = None  # Result message from connection test
        self.server_test_result_timer = 0  # Timer for result message
        self.server_testing = False  # Whether a test is in progress
        self.server_selected_index = 0  # Selected button index (0=address, 1=port, 2=test, 3=connect, 4=back)
        
        # Password authentication variables
        self.authenticating_profile = None  # Profile name being authenticated
        self.password_input = None
        self.password_error = False
        self.password_error_timer = 0
        self.new_profile_name = None  # Store username for new profile creation
        
        # Visual effects for weapons
        self.camera_shake_intensity = 0  # Intensity of screen shake (0 = none)
        self.camera_shake_duration = 0   # Frames remaining for shake effect
        self.atomic_bomb_flash = 0       # Alpha value for white flash (0-255)
        self.game_background = None       # Procedural background for the play scene
        
        # Network performance tracking
        self.waiting_start_time = None
        self.last_state_time = time.time()
        self.missed_updates = 0  # Default server port (may be overridden by CLI args)
        
        # These systems are only fully active on the client
        if not self.is_server:
            self.particle_system = ParticleSystem()
            self.stars = self.create_starfield()
            self.hud = HUD(self.assets)
            self.shop = Shop(self.assets)
            self.game_background = self.assets.get_level_background(self.current_level)
            self._init_loading_list()
            # Connect the shape renderer to the asset manager so sprites can be loaded
            ShapeRenderer.set_asset_manager(self.assets)
        else:
            self.particle_system = None
            self.stars = []
            self.hud = None
            self.shop = None

        # --- 4. System Initialization ---
        # Load configs (needed for hitbox/behavior logic on server)
        EnemyFactory.load_configs('data/enemies.json')
        BulletFactory.load_configs('data/weapons.json')

    def _init_loading_list(self):
        """Create list of items to load during splash screen"""
        self.loading_items = [
            "Initializing core systems...",
            "Loading fonts and assets...",
            "Loading sound effects...",
            "Loading sprites...",
            "Loading enemy configurations...",
            "Loading weapon configurations...",
            "Preparing game world...",
        ]
        self.loading_items_total = len(self.loading_items)

    def _refresh_player_drone(self):
        """Spawn or refresh the player's support drones."""
        self.drones.empty()
        if self.player and getattr(self.player, "drone_level", 0) > 0:
            offsets = [-60, 60]
            for offset in offsets:
                drone = Drone(self.player, self.player.drone_level, offset_x=offset)
                self.drones.add(drone)

    def _sync_player_drone(self):
        """Ensure the player's drones match the unlocked drone level."""
        if not self.player:
            return
        desired_level = getattr(self.player, "drone_level", 0)
        current_drone = next(iter(self.drones), None)
        if desired_level <= 0:
            if current_drone:
                self.drones.empty()
            return
        if (
            current_drone is None
            or current_drone.level != desired_level
            or len(self.drones) != 2
        ):
            self._refresh_player_drone()

    def _update_drones(self):
        """Update all support drones and let them fire at enemies."""
        self._sync_player_drone()
        for drone in list(self.drones):
            drone.update()
            drone.try_fire(self.enemies, self.bullets, self.all_sprites)

    def _init_game(self):
        # In network mode, the client doesn't initialize the game, the server does.
        if self.is_network_mode:
            return

        """Legacy method for profile-based game initialization. Routes to init_game()."""
        if self.profile:
            self.current_profile = self.profile
        self.init_game()

    def generate_daily_challenge(self):
        """Generate or refresh the player's daily challenge."""
        today = time.strftime("%Y-%m-%d")
        if not self.current_profile:
            return None

        if self.current_profile.daily_challenge_date != today:
            self.current_profile.daily_challenge_date = today
            self.current_profile.daily_challenge_completed = False
            challenge_choices = [
                {"title": "Clear 2 levels", "description": "Complete 2 levels in one session.", "reward": 50},
                {"title": "Collect 150 coins", "description": "Earn 150 coins during a run.", "reward": 75},
                {"title": "Defeat 30 enemies", "description": "Destroy 30 enemies before taking a hit.", "reward": 100},
                {"title": "Survive 5 minutes", "description": "Keep your ship alive for 5 minutes.", "reward": 80},
            ]
            self.daily_challenge = random.choice(challenge_choices)
            self.current_profile.daily_challenge_date = today
            self.current_profile.daily_challenge_completed = False
        return self.daily_challenge

    def check_daily_challenge_completion(self):
        """Check if the current session has completed the daily challenge."""
        if not self.current_profile or not self.daily_challenge:
            return False

        title = self.daily_challenge.get("title", "")
        if title == "Clear 2 levels":
            completed = self.current_level > 2
        elif title == "Collect 150 coins":
            completed = self.player.coins - getattr(self.current_profile, 'session_start_coins', 0) >= 150
        elif title == "Defeat 30 enemies":
            completed = getattr(self.player, 'kills', 0) >= 30
        elif title == "Survive 5 minutes":
            completed = time.time() - self.session_start_time >= 300
        else:
            completed = False

        if completed and not self.current_profile.daily_challenge_completed:
            self.current_profile.daily_challenge_completed = True
            reward = self.daily_challenge.get("reward", 0)
            self.current_profile.total_coins += reward
            self.player.coins += reward
            logger.info(
                f"Daily challenge completed: {self.daily_challenge['title']} - reward {reward} coins"
            )
        return completed

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return # Exit early
            
            # --- State-based Event Handling ---
            
            if self.state == GameState.SPLASH_SCREEN:
                if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                    if self.splash_ready:
                        # Go directly to username/password entry instead of listing profiles
                        self.state = GameState.NAME_INPUT
                        self.splash_skipped = True
                        self.text_input = TextInput(
                            game_config.SCREEN_WIDTH // 2 - 200, 350, 400, 60,
                            self.assets.fonts['medium'], placeholder="Profile Name")
            
            elif self.state == GameState.NAME_INPUT:
                if self.text_input:
                    result = self.text_input.handle_event(event)
                    if result:
                        profile_name = result.strip()
                        if profile_name:
                            self.new_profile_name = profile_name
                            self.authenticating_profile = profile_name
                            self.state = GameState.PASSWORD_INPUT
                            self.password_input = TextInput(
                                game_config.SCREEN_WIDTH // 2 - 150, 350, 300, 60,
                                self.assets.fonts['medium'], is_password=True, placeholder="Password")
                            self.text_input = None
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        # Cancel profile creation, go back to profile select
                        self.state = GameState.PROFILE_SELECT
                        self.creating_new_profile = False

            elif self.state == GameState.PROFILE_SELECT:
                if event.type == pygame.KEYDOWN:
                    if self.server_socket:
                        try:
                            self.server_socket.close()
                        except Exception:
                            pass
                    self.state = GameState.NAME_INPUT
                    self.text_input = TextInput(
                        game_config.SCREEN_WIDTH // 2 - 200, 350, 400, 60,
                        self.assets.fonts['medium'], placeholder="Profile Name")
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.state = GameState.NAME_INPUT
                    self.text_input = TextInput(
                        game_config.SCREEN_WIDTH // 2 - 200, 350, 400, 60,
                        self.assets.fonts['medium'], placeholder="Profile Name")

            elif self.state == GameState.PASSWORD_INPUT:
                if self.password_input:
                    result = self.password_input.handle_event(event)
                    if result is not None:
                        password = result.strip()
                        profile_name = self.new_profile_name or self.authenticating_profile
                        if profile_name and SaveSystem.profile_exists(profile_name):
                            if SaveSystem.verify_password(profile_name, password):
                                profile = SaveSystem.load_profile(profile_name)
                                self.profile = profile
                                self._apply_profile_start_level(profile)
                                self.new_profile_name = None
                                self.state = GameState.MAIN_MENU
                            else:
                                self.password_error = True
                                self.password_error_timer = 180  # 3 seconds at 60 FPS
                                self.password_input = TextInput(
                                    game_config.SCREEN_WIDTH // 2 - 150, 350, 300, 60,
                                    self.assets.fonts['medium'], is_password=True, placeholder="Password")
                        else:
                            self.profile = PlayerProfile(profile_name, password)
                            SaveSystem.save_profile(self.profile)
                            self._apply_profile_start_level(self.profile)
                            self.new_profile_name = None
                            self.state = GameState.MAIN_MENU
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        if self.new_profile_name:
                            self.new_profile_name = None
                            self.state = GameState.NAME_INPUT
                            self.text_input = TextInput(
                                game_config.SCREEN_WIDTH // 2 - 200, 350, 400, 60,
                                self.assets.fonts['medium'], placeholder="Profile Name")
                        else:
                            self.state = GameState.PROFILE_SELECT
                            self.authenticating_profile = None
                        self.password_input = None
                        self.password_error = False

            elif self.state == GameState.MAIN_MENU:
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_UP, pygame.K_w]:
                        self.menu_selected_index = (self.menu_selected_index - 1) % len(self.menu_buttons)
                    elif event.key in [pygame.K_DOWN, pygame.K_s]:
                        self.menu_selected_index = (self.menu_selected_index + 1) % len(self.menu_buttons)
                    elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                        if self.menu_buttons:
                            _, action = self.menu_buttons[self.menu_selected_index]
                            self._handle_menu_action(action)
                    elif event.key == pygame.K_ESCAPE:
                        self.state = GameState.QUIT_CONFIRM
                        self.quit_confirm_context = 'game'
                        self.quit_confirm_selected = False
                elif event.type == pygame.MOUSEMOTION:
                    mouse_pos = event.pos
                    for i, (button_rect, action) in enumerate(self.menu_buttons):
                        if button_rect.collidepoint(mouse_pos):
                            self.menu_selected_index = i
                            break
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for i, (button_rect, action) in enumerate(self.menu_buttons):
                        if button_rect.collidepoint(event.pos):
                            self.menu_selected_index = i
                            self._handle_menu_action(action)
                            break

            elif self.state == GameState.PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_q, pygame.K_ESCAPE]:
                        self.state = GameState.QUIT_CONFIRM
                        self.quit_confirm_context = 'stage'
                        self.quit_confirm_selected = False
                    elif event.key == pygame.K_p:
                        self.state = GameState.PAUSED
                    elif event.key in [pygame.K_e, pygame.K_TAB]:
                        # Cycle to next weapon
                        if self.player and self.player.weapons:
                            self.player.cycle_weapon_next()
                            logger.info(f"Weapon changed to: {self.player.get_selected_weapon()}")
                    elif event.key == pygame.K_b:
                        # Activate selected weapon (atomic bomb, enemy freeze, etc.)
                        if self.player:
                            weapon = self.player.get_selected_weapon()
                            if weapon == 'atomic_bomb':
                                # Check if player has atomic bombs available
                                if not self.player.has_weapon('atomic_bomb'):
                                    logger.warning("No atomic bombs available!")
                                    self.assets.play_sound('menu_select', 0.5)  # Error feedback
                                    continue  # skip to next event, don't break the loop
                                # Use the atomic bomb (decrement count)
                                self.player.use_weapon('atomic_bomb')
                                
                                # Clear all enemies from the level
                                logger.info("⚡ ATOMIC BOMB ACTIVATED! Destroying all enemies!")
                                self.assets.play_sound('explosion', 0.9)
                                
                                # Trigger visual effects
                                self.camera_shake_intensity = 15  # Strong shake
                                self.camera_shake_duration = 30   # 0.5 seconds at 60 FPS
                                self.atomic_bomb_flash = 200      # Bright white flash
                                
                                # Collect enemies list first to avoid modifying during iteration
                                enemies_to_destroy = list(self.enemies)
                                for enemy in enemies_to_destroy:
                                    coins_reward = random.randint(5, 15)
                                    self.player.coins += coins_reward
                                    multiplier = self.player.add_kill_combo()
                                    score = int(enemy.max_health * 10 * multiplier)
                                    self.player.score += score
                                    # Create explosion particles at enemy location
                                    self.particle_system.emit_explosion(
                                        enemy.rect.centerx, enemy.rect.centery,
                                        color_config.YELLOW, count=15
                                    )
                                    # Remove from all_sprites so they disappear immediately
                                    enemy.kill()
                                self.enemies.empty()
                            elif weapon == 'enemy_freeze':
                                # Check if player has enemy freeze available
                                if not self.player.has_weapon('enemy_freeze'):
                                    logger.warning("No enemy freeze available!")
                                    self.assets.play_sound('menu_select', 0.5)  # Error feedback
                                    continue  # skip to next event
                                # Use the enemy freeze (decrement count)
                                self.player.use_weapon('enemy_freeze')

                                logger.info("❄️ ENEMY FREEZE ACTIVATED! Freezing all enemies!")
                                self.assets.play_sound('powerup', 0.7)
                                for enemy in self.enemies:
                                    if not hasattr(enemy, 'frozen_timer'):
                                        enemy.frozen_timer = 0
                                    enemy.frozen_timer = 300  # 5 seconds at 60 FPS
                            elif weapon == 'shockwave':
                                if not self.player.has_weapon('shockwave'):
                                    logger.warning("No shockwave weapon available!")
                                    self.assets.play_sound('menu_select', 0.5)
                                    continue  # skip to next event
                                self.player.use_weapon('shockwave')

                                logger.info("🌊 SHOCKWAVE ACTIVATED!")
                                self.assets.play_sound('explosion', 0.8)
                                self.camera_shake_intensity = 14
                                self.camera_shake_duration = 26
                                enemies_list = list(self.enemies)
                                for enemy in enemies_list:
                                    dx = enemy.rect.centerx - self.player.rect.centerx
                                    dy = enemy.rect.centery - self.player.rect.centery
                                    dist = max(1, math.sqrt(dx*dx + dy*dy))
                                    damage = max(40, int(280 / (dist / 40)))
                                    enemy.health -= damage
                                    push_x = int(dx / dist * 100)
                                    push_y = int(dy / dist * 100)
                                    enemy.rect.x += push_x
                                    enemy.rect.y += push_y
                                    self.particle_system.emit_explosion(
                                        enemy.rect.centerx, enemy.rect.centery,
                                        color_config.CYAN, count=12)
                                    if enemy.health <= 0:
                                        self.player.coins += random.randint(5, 15)
                                        multiplier = self.player.add_kill_combo()
                                        self.player.score += int(enemy.max_health * 10 * multiplier)
                                        enemy.kill()
                            elif weapon == 'chain_lightning':
                                if not self.player.has_weapon('chain_lightning'):
                                    logger.warning("No chain lightning weapon available!")
                                    self.assets.play_sound('menu_select', 0.5)
                                    continue  # skip to next event
                                self.player.use_weapon('chain_lightning')

                                logger.info("⚡ CHAIN LIGHTNING ACTIVATED!")
                                self.assets.play_sound('powerup', 0.8)
                                enemies_list = list(self.enemies)
                                if enemies_list:
                                    enemies_list.sort(key=lambda e: math.sqrt(
                                        (e.rect.centerx - self.player.rect.centerx)**2 +
                                        (e.rect.centery - self.player.rect.centery)**2))
                                    chain_targets = enemies_list[:5]
                                    chain_damage = 80
                                    for enemy in chain_targets:
                                        enemy.health -= chain_damage
                                        self.particle_system.emit_explosion(
                                            enemy.rect.centerx, enemy.rect.centery,
                                            color_config.YELLOW, count=12)
                                        if enemy.health <= 0:
                                            self.player.coins += random.randint(5, 15)
                                            multiplier = self.player.add_kill_combo()
                                            self.player.score += int(enemy.max_health * 10 * multiplier)
                                            enemy.kill()
                                        chain_damage = int(chain_damage * 0.7)
                            elif weapon == 'time_warp':
                                if not self.player.has_weapon('time_warp'):
                                    logger.warning("No time warp weapon available!")
                                    self.assets.play_sound('menu_select', 0.5)
                                    continue  # skip to next event
                                self.player.use_weapon('time_warp')

                                logger.info("💫 TIME WARP ACTIVATED! Slowing all enemies!")
                                self.assets.play_sound('powerup', 0.7)
                                for enemy in self.enemies:
                                    enemy.slow_timer = 300  # 5 seconds
                                    enemy.slow_factor = 0.25  # 25% speed
                                    self.particle_system.emit_explosion(
                                        enemy.rect.centerx, enemy.rect.centery,
                                        color_config.PURPLE, count=5)
                            elif weapon == 'spread_burst':
                                if not self.player.has_weapon('spread_burst'):
                                    logger.warning("No spread burst weapon available!")
                                    self.assets.play_sound('menu_select', 0.5)
                                    continue  # skip to next event
                                self.player.use_weapon('spread_burst')

                                logger.info("🎯 SPREAD BURST ACTIVATED!")
                                self.assets.play_sound('shoot', 0.9)
                                for angle in range(-55, 56, 10):
                                    bullet = BulletFactory.create(
                                        'default', self.player.rect.centerx,
                                        self.player.rect.top, -12,
                                        self.player.damage, angle)
                                    if bullet:
                                        self.bullets.add(bullet)
                                        self.all_sprites.add(bullet)
                                        self.particle_system.emit_trail(
                                            bullet.rect.centerx, bullet.rect.centery,
                                            color_config.ORANGE)
                            elif weapon == 'meteor_strike':
                                if not self.player.has_weapon('meteor_strike'):
                                    logger.warning("No meteor strike weapon available!")
                                    self.assets.play_sound('menu_select', 0.5)
                                    continue  # skip to next event
                                self.player.use_weapon('meteor_strike')

                                logger.info("☄️ METEOR STRIKE ACTIVATED!")
                                self.assets.play_sound('explosion', 0.9)
                                self.camera_shake_intensity = 12
                                self.camera_shake_duration = 25
                                self.atomic_bomb_flash = 120
                                enemies_list = list(self.enemies)
                                if enemies_list:
                                    import random as _rng
                                    targets = _rng.sample(enemies_list, min(3, len(enemies_list)))
                                    for enemy in targets:
                                        enemy.health -= 150
                                        self.particle_system.emit_explosion(
                                            enemy.rect.centerx, enemy.rect.centery,
                                            color_config.RED, count=25)
                                        self.particle_system.emit_explosion(
                                            enemy.rect.centerx, enemy.rect.centery,
                                            color_config.ORANGE, count=20)
                                        if enemy.health <= 0:
                                            self.player.coins += _rng.randint(10, 25)
                                            multiplier = self.player.add_kill_combo()
                                            self.player.score += int(enemy.max_health * 10 * multiplier)
                                            enemy.kill()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.player:
                        # In network mode, shooting is sent as an input event
                        if not self.is_network_mode:
                            bullets = self.player.shoot()
                            if bullets:
                                self.bullets.add(*bullets)
                                self.all_sprites.add(*bullets)
                                self.assets.play_sound('shoot', 0.5)
            
            elif self.state == GameState.PAUSED:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    self.state = GameState.PLAYING

            elif self.state == GameState.SHOP:
                # For simplicity, multiplayer shop is not implemented in this example
                if self.is_network_mode:
                    self.state = GameState.MAIN_MENU
                    return

                if self.shop.handle_input(event, self.player):
                    # This block is entered when the shop is closed.
                    if self.current_profile and self.player:
                        logger.info("Shop closed. Saving any profile changes made in the shop.")
                        self.current_profile.sync_after_shop(self.player.coins)
                        SaveSystem.save_profile(self.current_profile)
                    else:
                        logger.info("Shop closed without an active profile. No save performed.")
                    self.state = GameState.MAIN_MENU

            elif self.state == GameState.QUIT_CONFIRM:
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_LEFT, pygame.K_a]:
                        self.quit_confirm_selected = False # Select NO
                    elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                        self.quit_confirm_selected = True # Select YES
                    elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                        if self.quit_confirm_selected: # YES
                            if self.quit_confirm_context == 'game':
                                self.running = False
                            else:
                                if self.current_profile:
                                    self.current_profile = SaveSystem.load_profile(self.current_profile.name)
                                self.all_sprites.empty()
                                self.state = GameState.MAIN_MENU
                        else: # NO
                            self.state = GameState.MAIN_MENU if self.quit_confirm_context == 'game' else GameState.PLAYING
                    elif event.key == pygame.K_ESCAPE:
                        self.state = GameState.MAIN_MENU if self.quit_confirm_context == 'game' else GameState.PLAYING
                elif event.type == pygame.MOUSEMOTION:
                    mouse_pos = event.pos
                    if self.quit_yes_rect and self.quit_yes_rect.collidepoint(mouse_pos):
                        self.quit_confirm_hovered = 'yes'
                        self.quit_confirm_selected = True
                    elif self.quit_no_rect and self.quit_no_rect.collidepoint(mouse_pos):
                        self.quit_confirm_hovered = 'no'
                        self.quit_confirm_selected = False
                    else:
                        self.quit_confirm_hovered = None
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.quit_yes_rect and self.quit_yes_rect.collidepoint(event.pos):
                        if self.quit_confirm_context == 'game':
                            self.running = False
                        else:
                            if self.current_profile:
                                self.current_profile = SaveSystem.load_profile(self.current_profile.name)
                            self.all_sprites.empty()
                            self.state = GameState.MAIN_MENU
                    elif self.quit_no_rect and self.quit_no_rect.collidepoint(event.pos):
                        self.state = GameState.MAIN_MENU if self.quit_confirm_context == 'game' else GameState.PLAYING

            elif self.state == GameState.SERVER_CONNECT:
                if event.type == pygame.KEYDOWN:
                    # Handle special keys (navigation and actions)
                    if event.key == pygame.K_ESCAPE:
                        # Go back to main menu
                        self.state = GameState.MAIN_MENU
                    elif event.key == pygame.K_TAB:
                        # Cycle through input fields/buttons
                        self.server_selected_index = (self.server_selected_index + 1) % 5
                    elif event.key == pygame.K_UP:
                        self.server_selected_index = max(0, self.server_selected_index - 1)
                    elif event.key == pygame.K_DOWN:
                        self.server_selected_index = min(4, self.server_selected_index + 1)
                    elif event.key == pygame.K_RETURN:
                        # Handle button actions based on selection
                        if self.server_selected_index == 2:
                            # Test Connection button
                            self._test_server_connection()
                        elif self.server_selected_index == 3:
                            # Connect button
                            self._connect_to_server_from_ui()
                        elif self.server_selected_index == 4:
                            # Back button
                            self.state = GameState.MAIN_MENU
                    elif event.key == pygame.K_1:
                        self.server_selected_index = 0
                    elif event.key == pygame.K_2:
                        self.server_selected_index = 1
                    elif event.key == pygame.K_3:
                        self.server_selected_index = 2
                    elif event.key == pygame.K_4:
                        self.server_selected_index = 3
                    elif event.key == pygame.K_5:
                        self.server_selected_index = 4
                    else:
                        # Handle text input for selected field (for keys not handled above)
                        if self.server_selected_index == 0 and self.server_connect_input:
                            if event.key == pygame.K_BACKSPACE:
                                self.server_connect_input.text = self.server_connect_input.text[:-1]
                            elif len(self.server_connect_input.text) < self.server_connect_input.max_length:
                                if event.unicode.isprintable():
                                    self.server_connect_input.text += event.unicode
                        elif self.server_selected_index == 1 and self.server_port_input:
                            if event.key == pygame.K_BACKSPACE:
                                self.server_port_input.text = self.server_port_input.text[:-1]
                            elif len(self.server_port_input.text) < self.server_port_input.max_length:
                                if event.unicode.isdigit():
                                    self.server_port_input.text += event.unicode
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = event.pos
                    # Check input fields
                    if self.server_connect_input and self.server_connect_input.rect.collidepoint(mouse_pos):
                        self.server_selected_index = 0
                        self.server_connect_input.active = True
                        if self.server_port_input:
                            self.server_port_input.active = False
                    elif self.server_port_input and self.server_port_input.rect.collidepoint(mouse_pos):
                        self.server_selected_index = 1
                        self.server_port_input.active = True
                        self.server_connect_input.active = False
                    # Check buttons
                    elif self.server_test_button_rect and self.server_test_button_rect.collidepoint(mouse_pos):
                        self._test_server_connection()
                    elif self.server_connect_button_rect and self.server_connect_button_rect.collidepoint(mouse_pos):
                        self._connect_to_server_from_ui()
                    elif self.server_back_button_rect and self.server_back_button_rect.collidepoint(mouse_pos):
                        self.state = GameState.MAIN_MENU
                elif event.type == pygame.MOUSEMOTION:
                    # Update selection based on hover
                    mouse_pos = event.pos
                    if self.server_connect_input and self.server_connect_input.rect.collidepoint(mouse_pos):
                        self.server_selected_index = 0
                    elif self.server_port_input and self.server_port_input.rect.collidepoint(mouse_pos):
                        self.server_selected_index = 1
                    elif self.server_test_button_rect and self.server_test_button_rect.collidepoint(mouse_pos):
                        self.server_selected_index = 2
                    elif self.server_connect_button_rect and self.server_connect_button_rect.collidepoint(mouse_pos):
                        self.server_selected_index = 3
                    elif self.server_back_button_rect and self.server_back_button_rect.collidepoint(mouse_pos):
                        self.server_selected_index = 4

            elif self.state in [GameState.GAME_OVER, GameState.LEVEL_COMPLETE, GameState.HIGH_SCORES]:
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                        if self.state == GameState.LEVEL_COMPLETE:
                            self.current_level += 1
                            self.init_game()
                            self.state = GameState.PLAYING
                        else:
                            self.state = GameState.MAIN_MENU
                    elif event.key == pygame.K_ESCAPE:
                        if self.state == GameState.LEVEL_COMPLETE:
                            self.next_level_pending = True
                        self.state = GameState.MAIN_MENU

    # draw() was consolidated later in the file to keep a single canonical
    # rendering implementation that handles both local and networked clients.
    # The full `draw()` implementation appears further below.
    pass

    def create_starfield(self) -> List[Tuple[int, int, int]]:
        stars = []
        for _ in range(100):
            x = random.randint(0, game_config.SCREEN_WIDTH)
            y = random.randint(0, game_config.SCREEN_HEIGHT)
            size = random.randint(1, 3)
            stars.append((x, y, size))
        return stars
    
    def update_starfield(self):
        for i, (x, y, size) in enumerate(self.stars):
            y += size * 0.5
            if y - size > game_config.SCREEN_HEIGHT:
                y = -size
                x = random.randint(0, game_config.SCREEN_WIDTH)
            self.stars[i] = (x, y, size)
    
    def draw_starfield(self):
        for x, y, size in self.stars:
            brightness = 100 + (size * 50)
            color = (brightness, brightness, brightness)
            pygame.draw.circle(self.screen, color, (int(x), int(y)), size)

    def draw_progress_bar(self, x: int, y: int, width: int, height: int, progress: float, color):
        progress = max(0.0, min(1.0, progress))
        bg_rect = pygame.Rect(x, y, width, height)
        fg_rect = pygame.Rect(x + 2, y + 2, int((width - 4) * progress), height - 4)
        pygame.draw.rect(self.screen, (*color_config.UI_BORDER, 190), bg_rect, border_radius=10)
        pygame.draw.rect(self.screen, (*color, 190), fg_rect, border_radius=10)

    def create_random_background(self) -> pygame.Surface:
        """Generate a random space-themed background for the game scene."""
        width = game_config.SCREEN_WIDTH
        height = game_config.SCREEN_HEIGHT
        surface = pygame.Surface((width, height))

        # Pick a randomized gradient palette
        palettes = [
            ((8, 12, 30), (20, 60, 120)),
            ((10, 15, 40), (70, 18, 100)),
            ((12, 8, 35), (30, 100, 80)),
            ((20, 10, 30), (80, 40, 120)),
            ((4, 20, 50), (18, 80, 140)),
        ]
        start_color, end_color = random.choice(palettes)

        for y in range(height):
            t = y / max(1, height - 1)
            r = int(start_color[0] + (end_color[0] - start_color[0]) * t)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * t)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (width, y))

        # Add soft nebula glows
        for _ in range(random.randint(3, 5)):
            nebula_color = random.choice([
                (255, 120, 200),
                (120, 200, 255),
                (180, 80, 255),
                (255, 180, 80),
                (140, 255, 180),
            ])
            radius = random.randint(width // 6, width // 3)
            nebula_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                nebula_surface,
                (*nebula_color, random.randint(35, 65)),
                (radius, radius),
                radius,
            )
            nebula_x = random.randint(-radius // 2, width - radius // 2)
            nebula_y = random.randint(-radius // 2, height - radius // 2)
            surface.blit(nebula_surface, (nebula_x, nebula_y), special_flags=pygame.BLEND_ADD)

        # Add scattered star clusters and bright points
        for _ in range(random.randint(130, 200)):
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.choice([1, 1, 2])
            brightness = random.randint(120, 255)
            pygame.draw.circle(surface, (brightness, brightness, brightness), (x, y), size)

        for _ in range(random.randint(12, 20)):
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.randint(2, 4)
            brightness = random.randint(190, 255)
            pygame.draw.circle(surface, (brightness, brightness, brightness), (x, y), size)

        return surface

    def init_game(self):
        """Initialize or reset the game state for a new level."""
        self.all_sprites.empty()
        self.enemies.empty()
        self.bullets.empty()
        self.powerups.empty()

        if self.is_server:
            # Server mode: Add all pre-created players to the sprite group.
            # Player objects are managed by the server loop.
            self.all_sprites.add(*self.players)
        else:
            # Client/Single-player mode: Manage a single local player.
            if not self.player:
                self.player = Player(game_config.SCREEN_WIDTH // 2, game_config.SCREEN_HEIGHT - 100)
            
            self.player.health = self.player.max_health
            self.player.x = game_config.SCREEN_WIDTH // 2
            self.player.y = game_config.SCREEN_HEIGHT - 100
            
            if self.current_profile:
                self.current_profile.start_new_game()
                self.player.coins = self.current_profile.coins
                self.player.score = self.current_profile.score
                self.current_profile.apply_upgrades(self.player)
                self.daily_challenge = self.generate_daily_challenge()

            self.player.reset_combo()
            self.player.combo_multiplier = 1

            # Ensure the local player is part of the render/update sprite group.
            self.all_sprites.add(self.player)
            self._refresh_player_drone()
        self.level = Level(self.current_level)
        if self.assets:
            self.game_background = self.assets.get_level_background(self.current_level)
        self.session_start_time = time.time()

    def apply_server_state(self, state: dict):
        """Apply an authoritative server state to local sprite groups.
        This method is safe to call on server or client Game instances and
        is split out for easier testing and potential delta-updates later.
        """
        # Reset visible entity groups
        self.all_sprites.empty()
        self.players = []
        self.enemies.empty()
        self.bullets.empty()
        self.powerups.empty()

        # Players - FIXED: mark them as network_controlled=True
        for p_state in state.get('players', []):
            try:
                # CHANGED: Added network_controlled=True parameter
                p = Player(int(p_state.get('x', 0)), int(p_state.get('y', 0)), 
                        network_controlled=True)
                p.health = int(p_state.get('health', p.health))
                p.max_health = int(p_state.get('max_health', p.max_health))
                p.coins = int(p_state.get('coins', getattr(p, 'coins', 0)))
                p.score = int(p_state.get('score', getattr(p, 'score', 0)))
                self.players.append(p)
                self.all_sprites.add(p)
            except Exception:
                continue

        # Ensure the client's local player reference points to the authoritative
        # player object sent by the server (if we have a player_id).
        if not self.is_server:
            try:
                if self.player_id is not None and 0 <= int(self.player_id) < len(self.players):
                    self.player = self.players[int(self.player_id)]
                elif self.players and self.player is None:
                    self.player = self.players[0]
            except Exception:
                # defensive fallback
                if self.players and self.player is None:
                    self.player = self.players[0]

        # Enemies (server may use 'enemy_type')
        for e_state in state.get('enemies', []):
            try:
                etype = e_state.get('enemy_type') or e_state.get('type')
                # Accept either 'basic' or 'enemy_basic' naming from different sources/tests
                if isinstance(etype, str) and etype.startswith('enemy_'):
                    etype = etype.replace('enemy_', '')
                if not etype:
                    continue
                ex = int(e_state.get('x', 0))
                ey = int(e_state.get('y', 0))
                e = EnemyFactory.create(etype, ex, ey, 1, target=self.player)
                if e:
                    self.enemies.add(e)
                    self.all_sprites.add(e)
                    # Visual feedback for enemy spawn (client-side only)
                    if not self.is_server and self.particle_system:
                        self.particle_system.emit_explosion(ex, ey, color_config.RED, 10)
            except Exception:
                continue

        # Bullets
        for b_state in state.get('bullets', []):
            try:
                weapon = b_state.get('weapon_type', 'default')
                bx = int(b_state.get('x', 0))
                by = int(b_state.get('y', 0))
                speed = float(b_state.get('speed', -10))
                damage = int(b_state.get('damage', 1))
                angle = float(b_state.get('angle', 0))
                owner = b_state.get('owner', 'player')
                bullet = BulletFactory.create(
                    weapon, bx, by, speed, damage, angle,
                    {'owner': owner}
                )
                if bullet:
                    self.bullets.add(bullet)
                    self.all_sprites.add(bullet)
                    # Visual feedback for bullet (client-side only)
                    if not self.is_server and self.particle_system:
                        self.particle_system.emit_trail(bx, by, color_config.YELLOW)
            except Exception:
                # fallback placeholder bullet
                try:
                    bx = int(b_state.get('x', 0))
                    by = int(b_state.get('y', 0))
                    bullet = BulletFactory.create('default', bx, by, -10, 1, 0)
                    self.bullets.add(bullet)
                    self.all_sprites.add(bullet)
                except Exception:
                    pass

        # Power-ups
        for p_state in state.get('powerups', []):
            try:
                ptype = p_state.get('power_type', 'health')
                px = int(p_state.get('x', 0))
                py = int(p_state.get('y', 0))
                powerup = PowerUp(px, py, ptype)
                self.powerups.add(powerup)
                self.all_sprites.add(powerup)
                # Visual feedback for powerup spawn (client-side only)
                if not self.is_server and self.particle_system:
                    self.particle_system.emit_explosion(px, py, color_config.GREEN, 8)
            except Exception:
                continue

        # Keep a copy of the raw state for HUD rendering
        self.game_state_from_server = state


    def _delete_profile_at_index(self, idx: int):
        """Delete profile at given index from saved profiles and update UI state."""
        profiles = SaveSystem.get_profiles()
        if not profiles or idx < 0 or idx >= len(profiles):
            return False
        name = profiles[idx].name
        if SaveSystem.delete_profile(name):
            logger.info(f"Profile deleted: {name}")
            # Refresh internal lists
            self.existing_profiles = SaveSystem.get_profiles()
            # Adjust selected index
            if self.existing_profiles:
                self.profile_selected_index = min(idx, len(self.existing_profiles) - 1)
            else:
                # No profiles left - prompt for new name
                self.profile = None
                self.current_profile = None
                self.creating_new_profile = True
                self.state = GameState.NAME_INPUT
                self.text_input = TextInput(
                    game_config.SCREEN_WIDTH // 2 - 200, 350, 400, 60,
                    self.assets.fonts['medium'], placeholder="Profile Name")
            return True
        return False

    def _apply_profile_start_level(self, profile: 'PlayerProfile'):
        """Apply a selected profile and set the next starting level based
        on the profile's best (highest_level) value. Also initialize the player.
        """
        try:
            next_level = int(getattr(profile, 'highest_level', 1)) 
        except Exception:
            next_level = 1
        self.profile = profile
        self.current_profile = profile
        self.current_level = max(1, next_level)
        
        # Ensure a Player instance exists for this profile
        if not self.players:
            self.players.append(Player(game_config.SCREEN_WIDTH // 2, game_config.SCREEN_HEIGHT - 100))

        # If running as a client, keep `self.player` in sync with the profile-backed player
        if not self.is_server:
            # point local player reference to the authoritative player object created above
            self.player = self.players[0]

        # Always sync player's transient state (coins/score) from the selected profile
        if self.current_profile:
            # load saved session state so user can continue where they left off
            self.players[0].coins = self.current_profile.coins
            self.players[0].score = self.current_profile.score
            self.players[0].current_profile = self.current_profile
            self.players[0].profile = self.current_profile
            self.current_profile.apply_upgrades(self.players[0])
            if self.shop:
                self.shop.set_profile(self.current_profile)

    def save_and_exit(self):
        if self.current_profile and self.player:
            self.current_profile.coins = self.player.coins
            self.current_profile.score = self.player.score
            self.current_profile.current_level = self.current_level
            SaveSystem.save_profile(self.current_profile)
        logger.info("Game saved and exiting.")
        self.running = False
    
    def connect_to_server(self, host='127.0.0.1', port=65432):
        """Connects to the game server and sets network mode flag.
        Receives handshake with player_id assignment.
        Does NOT initialize game state or change the game state - caller must do that.
        """
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.connect((host, port))
            # Set timeout so recv doesn't block indefinitely
            # Allows send/receive to interleave on same socket
            self.server_socket.settimeout(0.05)  # 50ms for faster updates
            
            # Receive handshake from server with player assignment
            handshake = receive_data(self.server_socket)
            if handshake:
                print(f"received handshake {handshake}")
                self.player_id = handshake.get('player_id')
                logger.info(f"Received handshake from server: player_id={self.player_id}")
            else:
                logger.warning("Did not receive handshake from server")
            
            self.is_network_mode = True
            
            logger.info(f"Successfully connected to server at {host}:{port} as player {self.player_id}")
            return True
        except ConnectionRefusedError:
            logger.error(f"Connection to server at {host}:{port} refused. Is the server running?")
            self.is_network_mode = False
            return False
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            self.is_network_mode = False
            return False


    def update(self):
        """Update game state"""
        # Update UI state timer
        if self.duplicate_error_timer > 0:
            self.duplicate_error_timer -= 1
            if self.duplicate_error_timer == 0:
                self.duplicate_profile_error = False

        if self.state == GameState.SPLASH_SCREEN:
            # Play background music once
            if not self.background_music_playing:
                if not self.is_server:
                    self.assets.play_sound('splash', 0.2)  # Soft background music
                self.background_music_playing = True
            
            # Speed up loading progress (reduced wait time)
            # Shorter splash: ~3 seconds at 30 FPS
            if self.splash_loading_timer < 90:  # ~3 seconds at 30 FPS
                self.splash_loading_timer += 1
                self.loading_progress = min(
                    int((self.splash_loading_timer / 90) * self.loading_items_total),
                    self.loading_items_total - 1
                )
            else:
                # Loading complete
                self.splash_ready = True
                self.loading_progress = self.loading_items_total
            
            self.splash_timer += 2
            return
        
        if self.state == GameState.NAME_INPUT and self.text_input:
            self.text_input.update()
        
        # --- NETWORK CLIENT LOGIC (IMPROVED) ---
        if self.is_network_mode and self.state in (GameState.PLAYING, GameState.WAITING_FOR_PLAYERS):
            # Track waiting timeout protection
            if self.state == GameState.WAITING_FOR_PLAYERS:
                if self.waiting_start_time is None:
                    self.waiting_start_time = time.time()
                    logger.info("Entered waiting state, timeout tracking started")
                elif time.time() - self.waiting_start_time > 60:  # 60 second timeout
                    logger.warning("Waiting timeout exceeded - returning to main menu")
                    self.is_network_mode = False
                    self.state = GameState.MAIN_MENU
                    if self.server_socket:
                        try:
                            self.server_socket.close()
                        except:
                            pass
                        self.server_socket = None
                    return
            else:
                self.waiting_start_time = None  # Reset when not waiting

            # Play background music on first frame
            if self.state == GameState.PLAYING and not self.background_music_playing:
                if self.assets:
                    self.assets.play_sound('splash', 0.2)
                self.background_music_playing = True

            # 1. Send local input to server
            keys = pygame.key.get_pressed()
            mouse_buttons = pygame.mouse.get_pressed()
            input_payload = {'keys': [], 'shoot': False}
            
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                input_payload['keys'].append('a')
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                input_payload['keys'].append('d')
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                input_payload['keys'].append('w')
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                input_payload['keys'].append('s')
            if keys[pygame.K_SPACE] or mouse_buttons[0]:
                input_payload['shoot'] = True

            try:
                send_data(self.server_socket, input_payload)
            except ConnectionResetError:
                logger.error("Connection lost to server")
                self.is_network_mode = False
                self.state = GameState.MAIN_MENU
                if self.server_socket:
                    try:
                        self.server_socket.close()
                    except:
                        pass
                    self.server_socket = None
                return
            except Exception as e:
                logger.debug(f"Failed to send input (non-fatal): {e}")

            # 2. Receive game state from server (catch-up mechanism)
            states_received = 0
            max_states_per_frame = 3  # Process up to 3 states to catch up
            
            while states_received < max_states_per_frame:
                try:
                    received_state = receive_data(self.server_socket)
                    if received_state is not None:
                        states_received += 1
                        self.last_state_time = time.time()
                        self.missed_updates = 0
                        
                        # Process server state enum
                        enum_val = received_state.get('game_state_enum')
                        if isinstance(enum_val, int):
                            try:
                                server_state = GameState(enum_val)
                                if server_state == GameState.PLAYING and self.state == GameState.WAITING_FOR_PLAYERS:
                                    logger.info("Server state=PLAYING — switching client to PLAYING")
                                    self.state = GameState.PLAYING
                                elif server_state == GameState.WAITING_FOR_PLAYERS:
                                    self.state = GameState.WAITING_FOR_PLAYERS
                                elif server_state == GameState.GAME_OVER and self.state == GameState.PLAYING:
                                    logger.info("Server state=GAME_OVER — switching client to GAME_OVER")
                                    self.state = GameState.GAME_OVER
                            except Exception:
                                pass

                        self.game_state_from_server = received_state
                    else:
                        break
                except socket.timeout:
                    break
                except Exception as e:
                    logger.debug(f"Receive error (non-fatal): {e}")
                    break

            # Track connection health
            if states_received == 0:
                self.missed_updates += 1
                if self.missed_updates > 180:  # 6 seconds at 30 FPS
                    logger.error("No server updates for 6 seconds - connection lost")
                    self.is_network_mode = False
                    self.state = GameState.MAIN_MENU
                    if self.server_socket:
                        try:
                            self.server_socket.close()
                        except:
                            pass
                        self.server_socket = None
                    return

            # 3. Apply server state
            if self.game_state_from_server:
                self.apply_server_state(self.game_state_from_server)

            # Update sprites and particles
            self.all_sprites.update()
            if self.particle_system:
                self.particle_system.update()

            self.update_starfield()
            return

        # --- LOCAL SIMULATION LOGIC (if not in network mode) ---
        if self.is_network_mode:
            return # Should not run local simulation if connected to server

        if self.state == GameState.PLAYING:
            # Update visual effects
            if self.camera_shake_duration > 0:
                self.camera_shake_duration -= 1
            else:
                self.camera_shake_intensity = 0
            
            if self.atomic_bomb_flash > 0:
                self.atomic_bomb_flash -= 8  # Fade out the flash

            # Update the stage timer and end the level if time runs out.
            if self.level and not self.level.update_timer():
                if not self.is_server and self.current_profile:
                    if self.daily_challenge:
                        self.check_daily_challenge_completion()
                    coins_earned = self.player.coins - self.current_profile.session_start_coins
                    session_time = time.time() - self.session_start_time
                    self.current_profile.end_game(
                        self.player.score,
                        coins_earned,
                        self.current_level,
                        session_time
                    )
                    SaveSystem.save_profile(self.current_profile)
                if not self.is_server and self.assets:
                    self.assets.play_sound('level_complete', 0.8)
                self.state = GameState.LEVEL_COMPLETE
                return

            # Update sprites
            self.all_sprites.update()
            self._update_drones()
            if not self.is_server: # Particles are a client-side effect
                self.particle_system.update()
            
            # Player shooting (guard against null player after state change)
            if self.player:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_SPACE]:
                    new_bullets = self.player.shoot()
                    for bullet in new_bullets:
                        self.bullets.add(bullet)
                        self.all_sprites.add(bullet)
                        if not self.is_server:
                            self.particle_system.emit_trail(
                                bullet.rect.centerx, bullet.rect.centery, color_config.YELLOW)
            
            # Spawn boss once per level after the regular spawn wave is finished
            active_regular_enemies = len([e for e in self.enemies if e.enemy_type != 'boss'])
            if self.level.should_spawn_boss(active_regular_enemies):
                boss = EnemyFactory.create(
                    'boss',
                    random.randint(150, game_config.SCREEN_WIDTH - 150),
                    -160,  # higher entry for a dramatic reveal
                    self.current_level,
                    target=self.player
                )
                if boss:
                    self.enemies.add(boss)
                    self.all_sprites.add(boss)

            # Spawn enemies
            active_regular_enemies = len([e for e in self.enemies if e.enemy_type != 'boss'])
            if not self.level.boss_spawned and self.level.should_spawn_enemy(active_regular_enemies):
                enemy_type = EnemyFactory.get_random_type(self.current_level, self.level.wave_number)
                enemy = EnemyFactory.create(
                    enemy_type,
                    random.randint(50, game_config.SCREEN_WIDTH - 50),
                    -50, # y-position
                    self.current_level,
                    target=self.player
                )
                if enemy:
                    self.enemies.add(enemy)
                    self.all_sprites.add(enemy)
            
            # Spawn power-ups
            if self.level.should_spawn_powerup():
                power_type = random.choice([
                    'rapid_fire',
                    'shield',
                    'triple_shot',
                    'health',
                    'piercing',
                    'speed_boost',
                    'damage_boost',
                ])
                powerup = PowerUp(
                    random.randint(50, game_config.SCREEN_WIDTH - 50),
                    -30,
                    power_type
                )
                self.powerups.add(powerup)
                self.all_sprites.add(powerup)
            
# --- Player Collision Logic ---
            # This logic needs to handle both a single local player and multiple server-side players.
            players_to_check = self.players if self.is_server else ([self.player] if self.player else [])

            # Check bullet collisions for ownership-aware damage
            for bullet in list(self.bullets):
                owner = getattr(bullet, 'owner', 'player')
                if owner == 'player':
                    hit_enemies = pygame.sprite.spritecollide(bullet, self.enemies, False)
                    if hit_enemies:
                        if not getattr(bullet, 'piercing', False):
                            bullet.kill()
                        if not self.is_server:
                            self.assets.play_sound('enemy_hit', 0.7)
                        for enemy in hit_enemies:
                            enemy.health -= bullet.damage
                            if enemy.health <= 0:
                                if not self.is_server:
                                    self.particle_system.emit_explosion(
                                        enemy.rect.centerx, enemy.rect.centery,
                                        color_config.RED, 30)
                                    self.assets.play_sound('explosion', 0.8)
                                coins_gained = enemy.coin_value
                                if not self.is_server and self.player:
                                    multiplier = self.player.add_kill_combo()
                                    score_gained = int(enemy.score_value * multiplier)
                                    self.player.coins += coins_gained
                                    self.player.score += score_gained
                                elif self.is_server and self.players:
                                    score_gained = enemy.score_value
                                    self.players[0].coins += coins_gained
                                    self.players[0].score += score_gained
                                else:
                                    score_gained = enemy.score_value
                                logger.debug(
                                    f"Enemy destroyed. Player gained {coins_gained} coins, {score_gained} score. "
                                    f"Combo x{getattr(self.player, 'combo_multiplier', 1)}"
                                )
                                enemy.kill()
                            else:
                                if not self.is_server:
                                    self.particle_system.emit_explosion(
                                        bullet.rect.centerx, bullet.rect.centery,
                                        color_config.ORANGE, 10)
                else:
                    for player_obj in players_to_check:
                        if pygame.sprite.collide_rect(bullet, player_obj):
                            if not getattr(bullet, 'piercing', False):
                                bullet.kill()
                            player_obj.take_damage(bullet.damage)
                            if hasattr(player_obj, 'reset_combo'):
                                player_obj.reset_combo()
                            logger.info(f"Player hit by enemy projectile for {bullet.damage} damage.")
                            if not self.is_server and self.particle_system:
                                self.particle_system.emit_explosion(
                                    player_obj.rect.centerx, player_obj.rect.centery,
                                    color_config.RED, 15)
                            break

            # --- Player Collision Logic ---

            for player_obj in players_to_check:
                # Check player-enemy collisions
                hit_enemies = pygame.sprite.spritecollide(player_obj, self.enemies, True)
                for enemy in hit_enemies:
                    damage_taken = 30
                    player_obj.take_damage(damage_taken)
                    logger.info(f"Player collided with enemy. Took {damage_taken} damage. Health is now {player_obj.health}/{player_obj.max_health}.")
                    if not self.is_server:
                        self.particle_system.emit_explosion(
                            enemy.rect.centerx, enemy.rect.centery, color_config.RED, 25)
                    
                    if player_obj.health <= 0:
                        # On the server, we just mark the player as 'dead'. The client handles the 'Game Over' screen.
                        # In single-player, we transition the state.
                        if not self.is_server:
                            if self.assets:
                                self.assets.play_sound('game_over', 0.8)
                            if self.current_profile:
                                coins_earned = player_obj.coins - self.current_profile.session_start_coins
                                session_time = time.time() - self.session_start_time
                                self.current_profile.end_game(
                                    player_obj.score,
                                    coins_earned,
                                    self.current_level,
                                    session_time
                                )
                                SaveSystem.save_profile(self.current_profile)
                                SaveSystem.save_high_score(
                                    self.current_profile,
                                    player_obj.score,
                                    self.current_level
                                )
                            # In multiplayer, notify server that this client's game is over
                            if self.is_network_mode:
                                try:
                                    send_data(self.server_socket, {'message': 'game_over', 'player_id': self.player_id})
                                except Exception as e:
                                    logger.warning(f"Failed to notify server of game over: {e}")
                            self.state = GameState.GAME_OVER

                # Check player-powerup collisions
                hit_powerups = pygame.sprite.spritecollide(player_obj, self.powerups, True)
                for powerup in hit_powerups:
                    logger.info(f"Player collected power-up: '{powerup.power_type}'.")
                    player_obj.activate_powerup(powerup.power_type)
                    if not self.is_server:
                        self.assets.play_sound('powerup', 0.8)
                        self.particle_system.emit_explosion(
                            powerup.rect.centerx, powerup.rect.centery, color_config.GREEN, 20)
            
            # Check level complete
            if (self.level.enemies_spawned >= self.level.enemies_to_spawn and
                len(self.enemies) == 0):
                if not self.is_server and self.current_profile:
                    # This block was missing. It's crucial for saving progress.
                    if self.daily_challenge:
                        self.check_daily_challenge_completion()
                    coins_earned = self.player.coins - self.current_profile.session_start_coins
                    session_time = time.time() - self.session_start_time
                    self.current_profile.end_game(
                        self.player.score,
                        coins_earned,
                        self.current_level,
                        session_time
                    )
                    SaveSystem.save_profile(self.current_profile)

                if not self.is_server:
                    if self.assets:
                        self.assets.play_sound('level_complete', 0.8)
                self.state = GameState.LEVEL_COMPLETE
        
        # Always update starfield
        self.update_starfield()
    def draw(self):
        """Draw everything"""
        if self.is_server or not self.screen:
            return
        
        if self.state == GameState.SPLASH_SCREEN:
            self.screen.fill(color_config.BLACK)
        elif self.game_background:
            self.screen.blit(self.game_background, (0, 0))
            self.draw_starfield()
        else:
            self.screen.fill(color_config.BLACK)
            self.draw_starfield()
        
        if self.state == GameState.SPLASH_SCREEN:
            self.draw_splash_screen()
        
        elif self.state == GameState.NAME_INPUT:
            self.draw_name_input()
        
        elif self.state == GameState.PROFILE_SELECT:
            self.draw_profile_select()
        
        elif self.state == GameState.PASSWORD_INPUT:
            self.draw_password_input()
        
        elif self.state == GameState.MAIN_MENU:
            self.draw_main_menu()
        
        elif self.state == GameState.PLAYING:
            # Apply camera shake offset
            shake_offset_x = 0
            shake_offset_y = 0
            if self.camera_shake_intensity > 0:
                shake_offset_x = random.randint(-self.camera_shake_intensity, self.camera_shake_intensity)
                shake_offset_y = random.randint(-self.camera_shake_intensity, self.camera_shake_intensity)
            
            # Render either local-play or network-client view
            if (self.player and self.level) or self.is_network_mode:
                # Draw sprites with shake offset
                for sprite in self.all_sprites:
                    self.screen.blit(sprite.image, (sprite.rect.x + shake_offset_x, sprite.rect.y + shake_offset_y))

                for drone in self.drones:
                    self.screen.blit(drone.image, (drone.rect.x + shake_offset_x, drone.rect.y + shake_offset_y))

                for enemy in self.enemies:
                    # Draw health bar with shake offset
                    if enemy.health < enemy.max_health or enemy.frozen_timer > 0:
                        bar_width = enemy.rect.width
                        bar_height = 5
                        bar_x = enemy.rect.x + shake_offset_x
                        bar_y = enemy.rect.y + shake_offset_y - 10
                        
                        if enemy.frozen_timer > 0:
                            pygame.draw.rect(self.screen, color_config.CYAN,
                                           (bar_x, bar_y, bar_width, bar_height))
                            pygame.draw.rect(self.screen, color_config.WHITE,
                                           (bar_x, bar_y, bar_width, bar_height), 1)
                        else:
                            pygame.draw.rect(self.screen, color_config.RED,
                                           (bar_x, bar_y, bar_width, bar_height))
                            health_width = int(bar_width * (enemy.health / enemy.max_health))
                            pygame.draw.rect(self.screen, color_config.GREEN,
                                           (bar_x, bar_y, health_width, bar_height))

                if self.particle_system:
                    self.particle_system.draw(self.screen)

                # Draw atomic bomb flash effect
                if self.atomic_bomb_flash > 0:
                    flash_surface = pygame.Surface((game_config.SCREEN_WIDTH, game_config.SCREEN_HEIGHT))
                    flash_surface.fill(color_config.WHITE)
                    flash_surface.set_alpha(self.atomic_bomb_flash)
                    self.screen.blit(flash_surface, (0, 0))

                # Network client: HUD is driven by server-provided state
                if self.is_network_mode:
                    # Safe rendering: create temp player from server state (or use placeholder)
                    if self.game_state_from_server and isinstance(self.game_state_from_server, dict):
                        # Create minimal player object for HUD display
                        hud_player = Player(game_config.SCREEN_WIDTH // 2, game_config.SCREEN_HEIGHT - 100)
                        hud_player.score = int(self.game_state_from_server.get('score', 0))
                        hud_player.coins = int(self.game_state_from_server.get('coins', 0))
                        hud_player.has_shield = False
                        hud_player.rapid_fire = False
                        hud_player.triple_shot = False
                        
                        players_state = self.game_state_from_server.get('players', [])
                        if players_state and isinstance(players_state, list) and len(players_state) > 0:
                            p0 = players_state[0]
                            if isinstance(p0, dict):
                                hud_player.health = int(p0.get('health', hud_player.max_health))
                                hud_player.max_health = int(p0.get('max_health', hud_player.max_health))

                        self.hud.draw(
                            self.screen,
                            hud_player,
                            int(self.game_state_from_server.get('level', self.current_level)),
                            self.game_state_from_server.get('time_remaining', 0),
                            None,
                            combo_multiplier=1,
                            wave_number=int(self.game_state_from_server.get('wave_number', 1)),
                        )
                    else:
                        # Before first server state arrives: show placeholder HUD
                        if self.player:
                            elapsed = self.level.elapsed_time if self.level else 0
                            self.hud.draw(
                                self.screen,
                                self.player,
                                self.current_level,
                                elapsed,
                                None,
                                combo_multiplier=getattr(self.player, 'combo_multiplier', 1),
                                wave_number=self.level.wave_number if self.level else 1,
                            )
                else:
                    # Local single-player HUD
                    elapsed = self.level.elapsed_time if self.level else 0
                    self.hud.draw(
                        self.screen,
                        self.player,
                        self.current_level,
                        self.level.time_remaining if self.level else 0,
                        self.level.time_limit if self.level else None,
                        combo_multiplier=getattr(self.player, 'combo_multiplier', 1),
                        wave_number=self.level.wave_number if self.level else 1,
                    )
        
        elif self.state == GameState.PAUSED:
            if self.player:
                self.all_sprites.draw(self.screen)
                self.drones.draw(self.screen)
                self.draw_pause_screen()
        
        elif self.state == GameState.SHOP:
            if self.player:
                self.all_sprites.draw(self.screen)
                self.drones.draw(self.screen)
                self.shop.draw(self.screen, self.player)
        
        elif self.state == GameState.LEVEL_COMPLETE:
            self.draw_level_complete()
        
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over()
        
        elif self.state == GameState.HIGH_SCORES:
            self.draw_high_scores()
        
        elif self.state == GameState.QUIT_CONFIRM:
            if self.player:
                self.all_sprites.draw(self.screen)
                self.drones.draw(self.screen)
                for enemy in self.enemies:
                    enemy.draw_health_bar(self.screen)
                self.particle_system.draw(self.screen)
                self.draw_quit_confirm()
        
        # Handle the new waiting state
        elif self.state == GameState.WAITING_FOR_PLAYERS:
            self.draw_waiting_for_players()
        
        elif self.state == GameState.SERVER_CONNECT:
            self.draw_server_connect()

        pygame.display.flip()
        if self.state == GameState.WAITING_FOR_PLAYERS:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.is_network_mode = False
                        self.state = GameState.MAIN_MENU

    
    def draw_splash_screen(self):
        """Draw elegant splash screen with background image and loading progress"""
        center_x = game_config.SCREEN_WIDTH // 2
        center_y = game_config.SCREEN_HEIGHT // 2
        
        # Draw background image
        splash_image = self.assets.get_splash_image()
        if splash_image:
            self.screen.blit(splash_image, (0, 0))
        
        # Semi-transparent overlay for better text readability
        overlay = pygame.Surface((game_config.SCREEN_WIDTH, game_config.SCREEN_HEIGHT))
        overlay.fill(color_config.BLACK)
        overlay.set_alpha(120)
        self.screen.blit(overlay, (0, 0))
        
        # Draw animated decorative elements
        for i in range(3):
            radius = 80 + (i * 40) + int(math.sin(self.splash_timer * 0.03 + i) * 15)
            circle_alpha = max(0, 40 - (i * 15))
            circle_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(circle_surface, (*color_config.CYAN, circle_alpha), 
                             (radius, radius), radius, 2)
            circle_rect = circle_surface.get_rect(center=(center_x, center_y - 100))
            self.screen.blit(circle_surface, circle_rect)
        
        # Draw game logo - procedural spaceship design
        ship_points = [
            (center_x, center_y - 180),  # Top point
            (center_x - 25, center_y - 130),  # Left wing
            (center_x - 18, center_y - 115),  # Left inner
            (center_x - 12, center_y - 100),  # Left tail
            (center_x, center_y - 85),  # Bottom
            (center_x + 12, center_y - 100),  # Right tail
            (center_x + 18, center_y - 115),  # Right inner
            (center_x + 25, center_y - 130),  # Right wing
        ]
        
        # Draw glowing spaceship
        # for offset in [(3, 3), (-3, -3)]:
        #     glow_points = [(x + offset[0], y + offset[1]) for x, y in ship_points]
        #     pygame.draw.polygon(self.screen, (*color_config.CYAN, 60), glow_points)
        
        # pygame.draw.polygon(self.screen, color_config.CYAN, ship_points, 3)
        # pygame.draw.polygon(self.screen, color_config.WHITE, ship_points)
        
        # Title
        
        
        # if self.splash_timer < 10:
        #     self.text1 = " SPACE DEFENDER *"
        # elif self.splash_timer % 10 == 0:
        #     self.text1 = self.text1[1:] + self.text1[0] # "SPACE DEFENDER"
        # title_text = self.text1

        title_text = "SPACE DEFENDER" 



        title_font = self.assets.fonts['title']
        
        # Glow effect for title
        for offset in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
            glow_surface = title_font.render(title_text, True, color_config.CYAN)
            glow_surface.set_alpha(40)
            glow_rect = glow_surface.get_rect(center=(center_x + offset[0], center_y + 20 + offset[1]))
            self.screen.blit(glow_surface, glow_rect)
        
        title_surface = title_font.render(title_text, True, color_config.WHITE)
        title_rect = title_surface.get_rect(center=(center_x, center_y + 20))
        self.screen.blit(title_surface, title_rect)
        
        # Subtitle
        subtitle = self.assets.fonts['medium'].render("Defend Against Invaders", True, color_config.CYAN)
        subtitle_rect = subtitle.get_rect(center=(center_x, center_y + 70))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Loading section
        loading_bar_width = 450
        loading_bar_height = 25
        loading_bar_x = center_x - loading_bar_width // 2
        loading_bar_y = center_y + 150
        
        # Loading label
        loading_label = self.assets.fonts['medium'].render("LOADING...", True, color_config.CYAN)
        loading_label_rect = loading_label.get_rect(center=(center_x, loading_bar_y - 50))
        self.screen.blit(loading_label, loading_label_rect)
        
        # Draw loading bar background with gradient border
        pygame.draw.rect(self.screen, color_config.CYAN, 
                        (loading_bar_x - 2, loading_bar_y - 2, loading_bar_width + 4, loading_bar_height + 4), 3)
        pygame.draw.rect(self.screen, (30, 30, 60), 
                        (loading_bar_x, loading_bar_y, loading_bar_width, loading_bar_height))
        
        # Draw progress bar with animation
        progress_width = int((self.loading_progress / max(1, self.loading_items_total)) * loading_bar_width)
        if progress_width > 0:
            # Draw progress fill
            pygame.draw.rect(self.screen, color_config.GREEN, 
                            (loading_bar_x, loading_bar_y, progress_width, loading_bar_height))
            # Add shimmer effect
            shimmer_x = int((self.splash_timer % 60) / 60 * loading_bar_width)
            if 0 <= shimmer_x < loading_bar_width:
                pygame.draw.line(self.screen, color_config.WHITE,
                               (loading_bar_x + shimmer_x, loading_bar_y),
                               (loading_bar_x + shimmer_x, loading_bar_y + loading_bar_height), 2)
        
        # Loading percentage text
        progress_percentage = int((self.loading_progress / max(1, self.loading_items_total)) * 100)
        progress_text = self.assets.fonts['large'].render(f"{progress_percentage}%", True, color_config.YELLOW)
        progress_rect = progress_text.get_rect(center=(loading_bar_x + loading_bar_width // 2, 
                                                       loading_bar_y + loading_bar_height + 35))
        self.screen.blit(progress_text, progress_rect)
        
        # Current loading item
        if 0 <= self.loading_progress - 1 < len(self.loading_items):
            current_item = self.loading_items[self.loading_progress - 1]
        else:
            current_item = "Finalizing..."
        
        loading_text = self.assets.fonts['small'].render(current_item, True, color_config.UI_TEXT)
        loading_rect = loading_text.get_rect(center=(center_x, loading_bar_y - 25))
        self.screen.blit(loading_text, loading_rect)
        
        # Press to continue hint - only show when loading is complete
        if self.splash_ready:
            continue_text = "Click or press any key to continue..."
            continue_surface = self.assets.fonts['medium'].render(continue_text, True, color_config.YELLOW)
            continue_alpha = int(200 + 55 * math.sin(self.splash_timer * 0.08))  # Pulsing effect
            continue_surface.set_alpha(continue_alpha)
            continue_rect = continue_surface.get_rect(center=(center_x, game_config.SCREEN_HEIGHT - 80))
            self.screen.blit(continue_surface, continue_rect)
        
        # Creator info
        created_text = self.assets.fonts['tiny'].render(
            "Created by Ali Mortazavi • Shahid Beheshti School • 2026", True, color_config.UI_TEXT)
        created_text.set_alpha(150)
        created_rect = created_text.get_rect(center=(center_x, game_config.SCREEN_HEIGHT - 20))
        self.screen.blit(created_text, created_rect)
    
    def draw_name_input(self):
        """Draw name input screen for entering a profile name."""
        screen_w = game_config.SCREEN_WIDTH
        screen_h = game_config.SCREEN_HEIGHT

        overlay = pygame.Surface((screen_w, screen_h))
        overlay.fill(color_config.BLACK)
        overlay.set_alpha(220)
        self.screen.blit(overlay, (0, 0))

        box_width = min(680, screen_w - 40)
        box_height = min(420, screen_h - 40)
        box_x = (screen_w - box_width) // 2
        box_y = (screen_h - box_height) // 2

        pygame.draw.rect(self.screen, color_config.UI_BG, (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, color_config.CYAN, (box_x, box_y, box_width, box_height), 3)

        title = self.assets.fonts['large'].render("ENTER PROFILE NAME", True, color_config.GREEN)
        title_rect = title.get_rect(center=(screen_w // 2, box_y + int(box_height * 0.14)))
        self.screen.blit(title, title_rect)

        explanation = self.assets.fonts['medium'].render(
            "Enter your profile name, then set or enter a password.",
            True, color_config.WHITE)
        explanation_rect = explanation.get_rect(center=(screen_w // 2, box_y + int(box_height * 0.26)))
        self.screen.blit(explanation, explanation_rect)

        username_label = self.assets.fonts['medium'].render("Profile name:", True, color_config.UI_TEXT)
        username_label_rect = username_label.get_rect(topleft=(box_x + 40, box_y + int(box_height * 0.38)))
        self.screen.blit(username_label, username_label_rect)

        if self.text_input:
            # Position the text input field relative to the dialog box
            self.text_input.rect.x = box_x + 40
            self.text_input.rect.y = box_y + 200
            self.text_input.rect.width = box_width - 80
            self.text_input.draw(self.screen)

        hint1 = self.assets.fonts['small'].render(
            "If this name exists, you'll enter the password to access it.",
            True, color_config.UI_TEXT)
        hint1_rect = hint1.get_rect(center=(screen_w // 2, box_y + int(box_height * 0.66)))
        self.screen.blit(hint1, hint1_rect)

        hint2 = self.assets.fonts['small'].render(
            "If the name is new, a profile will be created.",
            True, color_config.UI_TEXT)
        hint2_rect = hint2.get_rect(center=(screen_w // 2, box_y + int(box_height * 0.74)))
        self.screen.blit(hint2, hint2_rect)

        hint3 = self.assets.fonts['small'].render(
            "Press ENTER to continue • ESC to cancel",
            True, color_config.UI_TEXT)
        hint3_rect = hint3.get_rect(center=(screen_w // 2, box_y + int(box_height * 0.86)))
        self.screen.blit(hint3, hint3_rect)
    
    def draw_profile_select(self):
        """Draw simplified profile selection prompt."""
        screen_w = game_config.SCREEN_WIDTH
        screen_h = game_config.SCREEN_HEIGHT

        overlay = pygame.Surface((screen_w, screen_h))
        overlay.fill(color_config.BLACK)
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))

        box_width = min(720, screen_w - 40)
        box_height = min(320, screen_h - 40)
        box_x = (screen_w - box_width) // 2
        box_y = (screen_h - box_height) // 2

        pygame.draw.rect(self.screen, color_config.UI_BG, (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, color_config.UI_BORDER, (box_x, box_y, box_width, box_height), 3)

        title = self.assets.fonts['large'].render("PROFILE LOGIN", True, color_config.CYAN)
        title_rect = title.get_rect(center=(screen_w // 2, box_y + 60))
        self.screen.blit(title, title_rect)

        subtitle = self.assets.fonts['medium'].render(
            "Enter your profile name and password on the next screen.",
            True, color_config.UI_TEXT)
        subtitle_rect = subtitle.get_rect(center=(screen_w // 2, box_y + 130))
        self.screen.blit(subtitle, subtitle_rect)

        prompt = self.assets.fonts['small'].render(
            "Press any key or click to continue to profile credentials.",
            True, color_config.WHITE)
        prompt_rect = prompt.get_rect(center=(screen_w // 2, box_y + 200))
        self.screen.blit(prompt, prompt_rect)

        warning = self.assets.fonts['small'].render(
            "No profile list will be shown. Use the name and password directly.",
            True, color_config.UI_TEXT)
        warning_rect = warning.get_rect(center=(screen_w // 2, box_y + 240))
        self.screen.blit(warning, warning_rect)
    
    def draw_password_input(self):
        """Draw password input screen with clear distinction between authentication and creation"""
        screen_w = game_config.SCREEN_WIDTH
        screen_h = game_config.SCREEN_HEIGHT

        profile_name = self.new_profile_name or self.authenticating_profile
        is_existing = bool(profile_name and SaveSystem.profile_exists(profile_name))
        is_creating = bool(profile_name) and not is_existing

        overlay = pygame.Surface((screen_w, screen_h))
        overlay.fill(color_config.BLACK)
        overlay.set_alpha(210)
        self.screen.blit(overlay, (0, 0))

        box_width = min(620, screen_w - 40)
        box_height = min(400, screen_h - 40)
        box_x = (screen_w - box_width) // 2
        box_y = (screen_h - box_height) // 2

        border_color = color_config.GREEN if is_creating else color_config.CYAN
        if self.password_error and not is_creating:
            border_color = color_config.RED

        pygame.draw.rect(self.screen, (*color_config.UI_BG, 220), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, border_color, (box_x, box_y, box_width, box_height), 4)

        title_text = "CREATE PROFILE" if is_creating else "AUTHENTICATE PROFILE"
        title_color = color_config.GREEN if is_creating else color_config.CYAN
        title = self.assets.fonts['large'].render(title_text, True, title_color)
        title_rect = title.get_rect(center=(screen_w // 2, box_y + 50))
        self.screen.blit(title, title_rect)

        explanation_text = (
            "No existing profile found. Set a password to create it."
            if is_creating else
            "This profile already exists. Enter the password to access it."
        )
        explanation = self.assets.fonts['medium'].render(explanation_text, True, color_config.WHITE)
        explanation_rect = explanation.get_rect(center=(screen_w // 2, box_y + 100))
        self.screen.blit(explanation, explanation_rect)

        username_label = self.assets.fonts['small'].render("Profile:", True, color_config.UI_TEXT)
        username_label_rect = username_label.get_rect(topleft=(box_x + 40, box_y + 150))
        self.screen.blit(username_label, username_label_rect)

        username_value = self.assets.fonts['medium'].render(
            profile_name or "", True,
            color_config.GREEN if is_creating else color_config.CYAN)
        username_value_rect = username_value.get_rect(topleft=(box_x + 40, box_y + 175))
        self.screen.blit(username_value, username_value_rect)

        pwd_label_text = "Set Password:" if is_creating else "Password:"
        pwd_label = self.assets.fonts['medium'].render(pwd_label_text, True, color_config.WHITE)
        pwd_label_rect = pwd_label.get_rect(topleft=(box_x + 40, box_y + 230))
        self.screen.blit(pwd_label, pwd_label_rect)

        if self.password_input:
            self.password_input.update()
            pwd_input_y = box_y + 270
            original_y = self.password_input.rect.y
            self.password_input.rect.y = pwd_input_y
            self.password_input.draw(self.screen)
            self.password_input.rect.y = original_y

        instructions_text = (
            "Choose a password and press ENTER to create your profile."
            if is_creating else
            "Enter your password • Press ENTER to submit • ESC to cancel"
        )
        instructions = self.assets.fonts['small'].render(instructions_text, True, color_config.UI_TEXT)
        instructions_rect = instructions.get_rect(center=(screen_w // 2, box_y + 340))
        self.screen.blit(instructions, instructions_rect)

        if self.password_error and not is_creating:
            if self.password_error_timer > 0:
                error_msg = self.assets.fonts['medium'].render(
                    "❌ Incorrect password. Press ESC to retry.",
                    True, color_config.RED)
                error_rect = error_msg.get_rect(center=(screen_w // 2, box_y + 380))
                self.screen.blit(error_msg, error_rect)
    
    def draw_main_menu(self):
        """Draw main menu (responsive layout)"""
        screen_w = game_config.SCREEN_WIDTH
        screen_h = game_config.SCREEN_HEIGHT
        title_y = int(screen_h * 0.14)

        title = self.assets.fonts['title'].render("SPACE DEFENDER", True, color_config.CYAN)
        title_rect = title.get_rect(center=(screen_w // 2, title_y))
        self.screen.blit(title, title_rect)

        self.menu_animation_phase += 0.04
        if self.menu_animation_phase > math.pi * 2:
            self.menu_animation_phase -= math.pi * 2

        # Player stats and daily challenge summary
        if self.current_profile:
            if self.daily_challenge is None:
                self.daily_challenge = self.generate_daily_challenge()

            welcome = self.assets.fonts['medium'].render(
                f"Welcome, {self.current_profile.name}!", True, color_config.GREEN)
            welcome_rect = welcome.get_rect(center=(screen_w // 2, title_y + 80))
            self.screen.blit(welcome, welcome_rect)

            stats_text = (
                f"Score: {self.current_profile.total_score}  |  "
                f"Coins: {self.current_profile.total_coins}  |  "
                f"Best Level: {self.current_profile.highest_level}"
            )
            stats = self.assets.fonts['small'].render(stats_text, True, color_config.UI_TEXT)
            stats_rect = stats.get_rect(center=(screen_w // 2, title_y + 120))
            self.screen.blit(stats, stats_rect)

            if self.daily_challenge:
                    # Place the challenge box to the right of the button panel.
                    # Pre-compute the panel right edge (panel_width=560 defined below).
                    _menu_panel_right = (screen_w + 560) // 2
                    ch_avail_w = screen_w - _menu_panel_right - 10
                    if ch_avail_w >= 100:
                        ch_box_w = min(340, ch_avail_w)
                        challenge_box = pygame.Rect(_menu_panel_right + 10, title_y + 40, ch_box_w, 160)
                        pygame.draw.rect(self.screen, (*color_config.UI_BG, 220), challenge_box, border_radius=18)
                        pygame.draw.rect(self.screen, color_config.CYAN, challenge_box, 2, border_radius=18)

                        challenge_title_label = self.assets.fonts['small'].render(
                            "Daily Challenge", True, color_config.YELLOW)
                        self.screen.blit(challenge_title_label, (challenge_box.left + 18, challenge_box.top + 18))

                        ch_title = self.daily_challenge['title']
                        challenge_desc = self.daily_challenge['description']
                        challenge_reward = self.daily_challenge['reward']
                        challenge_prefix = "COMPLETED: " if self.current_profile.daily_challenge_completed else "TODAY'S GOAL: "

                        challenge_text = self.assets.fonts['tiny'].render(
                            f"{challenge_prefix}{ch_title}", True, color_config.WHITE)
                        self.screen.blit(challenge_text, (challenge_box.left + 18, challenge_box.top + 52))

                        reward_text = self.assets.fonts['tiny'].render(
                            challenge_desc, True, color_config.UI_TEXT)
                        self.screen.blit(reward_text, (challenge_box.left + 18, challenge_box.top + 80))

                        progress_text = self.assets.fonts['small'].render(
                            f"Reward: {challenge_reward} coins", True, color_config.CYAN)
                        self.screen.blit(progress_text, (challenge_box.left + 18, challenge_box.top + 112))

                        if self.current_profile.daily_challenge_completed:
                            status_surface = self.assets.fonts['small'].render(
                                "Status: Completed", True, color_config.GREEN)
                        else:
                            status_surface = self.assets.fonts['small'].render(
                                "Status: In Progress", True, color_config.YELLOW)
                        self.screen.blit(status_surface, (challenge_box.left + 18, challenge_box.top + 138))

        ring_center = (screen_w // 2, title_y + 40)
        for i in range(4):
            radius = 110 + (i * 28) + int(math.sin(self.menu_animation_phase + i * 0.9) * 12)
            alpha = max(10, 80 - (i * 15))
            ring = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(ring, (*color_config.CYAN, alpha), (radius, radius), radius, 2)
            self.screen.blit(ring, ring.get_rect(center=ring_center))

        mouse_pos = pygame.mouse.get_pos()
        start_y = int(screen_h * 0.45)
        spacing = int(screen_h * 0.08)
        options = [
            ("PRESS ENTER TO START", pygame.K_RETURN, "play"),
        ]

        if self.server_host and self.server_port:
            options.append(("O - PLAY ONLINE", pygame.K_o, "play_online"))

        options.extend([
            ("S - SHOP", pygame.K_s, "shop"),
            ("H - HIGH SCORES", pygame.K_h, "scores"),
            ("ESC - QUIT", pygame.K_ESCAPE, "quit")
        ])

        panel_width = 560
        panel_height = len(options) * spacing + 40
        panel_rect = pygame.Rect(
            (screen_w - panel_width) // 2,
            start_y - 45,
            panel_width,
            panel_height,
        )
        pygame.draw.rect(self.screen, (*color_config.UI_BG, 220), panel_rect, border_radius=24)
        pygame.draw.rect(self.screen, color_config.UI_BORDER, panel_rect, 3, border_radius=24)

        self.menu_buttons = []

        for idx, (text, key, action) in enumerate(options):
            y = start_y + idx * spacing
            button_width = panel_width - 40
            button_height = 56
            button_rect = pygame.Rect(
                panel_rect.left + 20,
                y - button_height // 2,
                button_width,
                button_height,
            )
            hovered = button_rect.collidepoint(mouse_pos)
            selected = idx == self.menu_selected_index

            button_surface = pygame.Surface((button_width, button_height), pygame.SRCALPHA)
            if selected:
                pulse = 180 + int(math.sin(self.menu_animation_phase * 2.2 + idx) * 30)
                pygame.draw.rect(button_surface, (40, 40, pulse, 240), button_surface.get_rect(), border_radius=16)
                pygame.draw.rect(button_surface, color_config.WHITE, button_surface.get_rect(), 2, border_radius=16)
                text_color = color_config.WHITE  # White text is always readable on dark button
            elif hovered:
                pygame.draw.rect(button_surface, (*color_config.UI_BG, 220), button_surface.get_rect(), border_radius=16)
                pygame.draw.rect(button_surface, color_config.CYAN, button_surface.get_rect(), 2, border_radius=16)
                text_color = color_config.WHITE
            else:
                pygame.draw.rect(button_surface, (*color_config.UI_BG, 200), button_surface.get_rect(), border_radius=16)
                pygame.draw.rect(button_surface, color_config.UI_BORDER, button_surface.get_rect(), 2, border_radius=16)
                text_color = color_config.UI_TEXT

            self.screen.blit(button_surface, button_rect.topleft)

            option_surface = self.assets.fonts['medium'].render(text, True, text_color)
            option_rect = option_surface.get_rect(center=button_rect.center)
            self.screen.blit(option_surface, option_rect)

            if hovered and not selected:
                glow = pygame.Surface((button_width, button_height), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*color_config.CYAN, 40), glow.get_rect(), border_radius=16)
                self.screen.blit(glow, button_rect.topleft)

            self.menu_buttons.append((button_rect, action))

        tip_text = "Use arrows or mouse to navigate. Press ENTER to select."
        tip_surface = self.assets.fonts['small'].render(tip_text, True, color_config.UI_TEXT)
        tip_rect = tip_surface.get_rect(center=(screen_w // 2, panel_rect.bottom + 40))
        self.screen.blit(tip_surface, tip_rect)
    
    def draw_pause_screen(self):
        """Draw pause overlay"""
        overlay = pygame.Surface((game_config.SCREEN_WIDTH, game_config.SCREEN_HEIGHT))
        overlay.fill(color_config.BLACK)
        overlay.set_alpha(170)
        self.screen.blit(overlay, (0, 0))

        panel_width = 560
        panel_height = 260
        panel_x = (game_config.SCREEN_WIDTH - panel_width) // 2
        panel_y = (game_config.SCREEN_HEIGHT - panel_height) // 2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, (*color_config.UI_BG, 220), panel_rect, border_radius=20)
        pygame.draw.rect(self.screen, color_config.CYAN, panel_rect, 3, border_radius=20)

        paused_text = self.assets.fonts['title'].render("PAUSED", True, color_config.CYAN)
        paused_rect = paused_text.get_rect(center=(game_config.SCREEN_WIDTH // 2, panel_y + 60))
        self.screen.blit(paused_text, paused_rect)

        continue_text = self.assets.fonts['medium'].render(
            "Press P to Continue", True, color_config.WHITE)
        continue_rect = continue_text.get_rect(center=(game_config.SCREEN_WIDTH // 2, panel_y + 130))
        self.screen.blit(continue_text, continue_rect)

        help_text = self.assets.fonts['small'].render(
            "ESC: Quit to Menu | E: Cycle Weapon | B: Use Weapon", True, color_config.UI_TEXT)
        help_rect = help_text.get_rect(center=(game_config.SCREEN_WIDTH // 2, panel_y + 190))
        self.screen.blit(help_text, help_rect)
    
    def draw_quit_confirm(self):
        """Draw quit confirmation dialog with warning and Yes/No buttons"""
        screen_w = game_config.SCREEN_WIDTH
        screen_h = game_config.SCREEN_HEIGHT
        overlay = pygame.Surface((screen_w, screen_h))
        overlay.fill(color_config.BLACK)
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))

        center_x = screen_w // 2

        # Title and contextual messages
        if self.quit_confirm_context == 'stage':
            title = "LEAVE THIS STAGE?"
            message = "Are you sure you want to leave? If you leave, you will lose your points."
        else:
            title = "EXIT THE GAME?"
            message = "Are you sure you want to leave the game?"

        title_y = int(screen_h * 0.24)
        title_text = self.assets.fonts['title'].render(title, True, color_config.RED)
        title_rect = title_text.get_rect(center=(center_x, title_y))
        self.screen.blit(title_text, title_rect)

        warn_y = int(screen_h * 0.33)
        warn_text = self.assets.fonts['medium'].render(message, True, color_config.WHITE)
        warn_rect = warn_text.get_rect(center=(center_x, warn_y))
        self.screen.blit(warn_text, warn_rect)

        warning_y = int(screen_h * 0.38)
        warning = self.assets.fonts['small'].render(
            "Select YES to confirm or NO to continue.", True, color_config.UI_TEXT)
        warning_rect = warning.get_rect(center=(center_x, warning_y))
        self.screen.blit(warning, warning_rect)

        # Button dimensions
        button_width = max(100, int(screen_w * 0.12))
        button_height = max(44, int(screen_h * 0.065))
        button_y = int(screen_h * 0.50)
        button_spacing = max(100, int(screen_w * 0.15))

        yes_x = center_x - button_spacing
        no_x = center_x + button_spacing

        # Store button rects for mouse click handling
        self.quit_yes_rect = pygame.Rect(yes_x - button_width // 2, button_y - button_height // 2,
                                         button_width, button_height)
        self.quit_no_rect = pygame.Rect(no_x - button_width // 2, button_y - button_height // 2,
                                        button_width, button_height)

        # Draw buttons with selection/hover highlight
        yes_hover = self.quit_confirm_hovered == 'yes'
        no_hover = self.quit_confirm_hovered == 'no'
        yes_active = yes_hover or self.quit_confirm_selected
        no_active = no_hover or (not self.quit_confirm_selected)

        yes_color = color_config.RED if yes_active else (60, 60, 60)
        no_color = color_config.GREEN if no_active else (60, 60, 60)

        pygame.draw.rect(self.screen, yes_color, self.quit_yes_rect, border_radius=14)
        pygame.draw.rect(self.screen, color_config.WHITE, self.quit_yes_rect, 2, border_radius=14)
        yes_text = self.assets.fonts['medium'].render("YES", True, color_config.WHITE)
        yes_text_rect = yes_text.get_rect(center=self.quit_yes_rect.center)
        self.screen.blit(yes_text, yes_text_rect)

        pygame.draw.rect(self.screen, no_color, self.quit_no_rect, border_radius=14)
        pygame.draw.rect(self.screen, color_config.WHITE, self.quit_no_rect, 2, border_radius=14)
        no_text = self.assets.fonts['medium'].render("NO", True, color_config.WHITE)
        no_text_rect = no_text.get_rect(center=self.quit_no_rect.center)
        self.screen.blit(no_text, no_text_rect)

        if yes_hover:
            focus_rect = pygame.Rect(self.quit_yes_rect.inflate(16, 16))
        elif no_hover:
            focus_rect = pygame.Rect(self.quit_no_rect.inflate(16, 16))
        elif self.quit_confirm_selected:
            focus_rect = pygame.Rect(self.quit_yes_rect.inflate(12, 12))
        else:
            focus_rect = pygame.Rect(self.quit_no_rect.inflate(12, 12))
        pygame.draw.rect(self.screen, color_config.CYAN, focus_rect, 3, border_radius=18)

        instructions = self.assets.fonts['small'].render(
            "LEFT/A: No  |  RIGHT/D: Yes  |  ENTER: Confirm  |  ESC: Cancel",
            True, color_config.UI_BORDER)
        instructions_rect = instructions.get_rect(center=(center_x, int(screen_h * 0.62)))
        self.screen.blit(instructions, instructions_rect)
    
    def draw_level_complete(self):
        """Draw level complete screen"""
        self.screen.fill(color_config.BLACK)
        self.draw_starfield()
        
        screen_w = game_config.SCREEN_WIDTH
        screen_h = game_config.SCREEN_HEIGHT
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((*color_config.BLACK, 200))
        self.screen.blit(overlay, (0, 0))

        panel_width = 700
        panel_height = 460
        panel_x = (screen_w - panel_width) // 2
        panel_y = (screen_h - panel_height) // 2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, (*color_config.UI_BG, 230), panel_rect, border_radius=24)
        pygame.draw.rect(self.screen, color_config.CYAN, panel_rect, 3, border_radius=24)

        title = self.assets.fonts['large'].render(
            f"LEVEL {self.current_level} COMPLETE!", True, color_config.GREEN)
        title_rect = title.get_rect(center=(screen_w // 2, panel_y + 60))
        self.screen.blit(title, title_rect)

        coins_earned = self.player.coins - getattr(self.current_profile, 'session_start_coins', 0)
        coins_earned = max(coins_earned, 0)
        best_level = getattr(self.current_profile, 'highest_level', self.current_level)
        next_level = self.current_level + 1
        next_goal = f"Reach Level {next_level} to unlock tougher enemies."
        if self.current_level >= 5:
            next_goal = f"Survive Level {next_level} to earn a rare upgrade reward."

        left_x = panel_x + 50
        right_x = panel_x + panel_width - 370
        y = panel_y + 130

        summary_items = [
            ("Coins earned", f"{coins_earned}"),
            ("Total score", f"{self.player.score}"),
            ("Best level", f"{best_level}"),
            ("Next goal", next_goal),
        ]

        for label, value in summary_items:
            label_surface = self.assets.fonts['small'].render(label, True, color_config.UI_TEXT)
            value_surface = self.assets.fonts['medium'].render(value, True, color_config.WHITE if label != "Next goal" else color_config.CYAN)
            self.screen.blit(label_surface, (left_x, y))
            self.screen.blit(value_surface, (left_x, y + label_surface.get_height() + 4))
            y += label_surface.get_height() + value_surface.get_height() + 18

        if self.current_profile and self.current_profile.daily_challenge_completed:
            reward_value = self.daily_challenge.get('reward', 0)
            reward_surface = self.assets.fonts['medium'].render(
                f"Daily Challenge Reward: +{reward_value} coins", True, color_config.GREEN)
            self.screen.blit(reward_surface, (right_x, panel_y + 130))
            self.draw_progress_bar(right_x, panel_y + 180, 280, 24, 1.0, color_config.GREEN)
            reward_label = self.assets.fonts['small'].render("Challenge completed", True, color_config.UI_TEXT)
            self.screen.blit(reward_label, (right_x, panel_y + 210))
        else:
            challenge_box = pygame.Rect(right_x, panel_y + 130, 280, 140)
            pygame.draw.rect(self.screen, (*color_config.BLACK, 180), challenge_box, border_radius=18)
            pygame.draw.rect(self.screen, color_config.CYAN, challenge_box, 2, border_radius=18)
            status_title = self.assets.fonts['small'].render("Challenge Status", True, color_config.YELLOW)
            self.screen.blit(status_title, (right_x + 16, panel_y + 146))
            if self.daily_challenge:
                status_text = self.assets.fonts['tiny'].render(
                    self.daily_challenge['description'], True, color_config.UI_TEXT)
                self.screen.blit(status_text, (right_x + 16, panel_y + 176))
                self.draw_progress_bar(right_x + 16, panel_y + 220, 248, 18, 0.6, color_config.CYAN)
                progress_label = self.assets.fonts['tiny'].render("Keep going!", True, color_config.WHITE)
                self.screen.blit(progress_label, (right_x + 16, panel_y + 248))

        action_text = self.assets.fonts['medium'].render(
            "Press ENTER to Continue or ESC to return to the menu", True, color_config.CYAN)
        action_rect = action_text.get_rect(center=(screen_w // 2, panel_y + panel_height - 40))
        self.screen.blit(action_text, action_rect)
    
    def draw_game_over(self):
        """Draw game over screen"""
        self.screen.fill(color_config.BLACK)
        self.draw_starfield()

        screen_w = game_config.SCREEN_WIDTH
        screen_h = game_config.SCREEN_HEIGHT
        center_x = screen_w // 2

        title = self.assets.fonts['title'].render("GAME OVER", True, color_config.RED)
        title_rect = title.get_rect(center=(center_x, int(screen_h * 0.24)))
        self.screen.blit(title, title_rect)

        y = int(screen_h * 0.34)
        if self.current_profile:
            name_text = self.assets.fonts['medium'].render(
                self.current_profile.name, True, color_config.CYAN)
            name_rect = name_text.get_rect(center=(center_x, y))
            self.screen.blit(name_text, name_rect)
            y += name_text.get_height() + int(screen_h * 0.04)

        if self.player:
            final_score = self.assets.fonts['large'].render(
                f"Final Score: {self.player.score}", True, color_config.WHITE)
            score_rect = final_score.get_rect(center=(center_x, y))
            self.screen.blit(final_score, score_rect)
            y += final_score.get_height() + int(screen_h * 0.04)

            coins_text = self.assets.fonts['medium'].render(
                f"Total Coins Earned: {self.player.coins}", True, color_config.YELLOW)
            coins_rect = coins_text.get_rect(center=(center_x, y))
            self.screen.blit(coins_text, coins_rect)
            y += coins_text.get_height() + int(screen_h * 0.04)

            level_text = self.assets.fonts['medium'].render(
                f"Reached Level: {self.current_level}", True, color_config.CYAN)
            level_rect = level_text.get_rect(center=(center_x, y))
            self.screen.blit(level_text, level_rect)

        continue_text = self.assets.fonts['medium'].render(
            "Press ENTER or ESC to Return to Menu", True, color_config.WHITE)
        continue_rect = continue_text.get_rect(center=(center_x, int(screen_h * 0.78)))
        self.screen.blit(continue_text, continue_rect)
    
    def draw_high_scores(self):
        """Draw high scores screen"""
        self.screen.fill(color_config.BLACK)
        self.draw_starfield()

        screen_w = game_config.SCREEN_WIDTH
        screen_h = game_config.SCREEN_HEIGHT
        center_x = screen_w // 2

        title = self.assets.fonts['title'].render("HIGH SCORES", True, color_config.CYAN)
        title_rect = title.get_rect(center=(center_x, int(screen_h * 0.13)))
        self.screen.blit(title, title_rect)

        scores = SaveSystem.get_high_scores()

        # Consolidate so a profile name is shown only once (keeping their best score)
        best_scores_map = {}
        for entry in scores:
            name = entry['name']
            # if name is not in map or if this score is strictly better
            if name not in best_scores_map or entry['score'] > best_scores_map[name]['score']:
                best_scores_map[name] = entry
                
        # Sort consolidated scores by score descending
        consolidated_scores = sorted(list(best_scores_map.values()), key=lambda x: x['score'], reverse=True)

        if not consolidated_scores:
            no_scores = self.assets.fonts['medium'].render(
                "No high scores yet!", True, color_config.WHITE)
            no_scores_rect = no_scores.get_rect(center=(center_x, screen_h // 2))
            self.screen.blit(no_scores, no_scores_rect)
        else:
            y_offset = int(screen_h * 0.27)
            row_height = int(screen_h * 0.08)
            col_rank = int(screen_w * 0.14)
            col_name = int(screen_w * 0.22)
            col_score = int(screen_w * 0.50)
            col_level = int(screen_w * 0.72)
            for i, entry in enumerate(consolidated_scores[:5]):
                rank_surface = self.assets.fonts['medium'].render(f"{i + 1}.", True, color_config.YELLOW)
                name_surface = self.assets.fonts['medium'].render(entry['name'], True, color_config.CYAN)
                score_surface = self.assets.fonts['medium'].render(f"Score: {entry['score']}", True, color_config.WHITE)
                level_surface = self.assets.fonts['small'].render(f"Level: {entry['level']}", True, color_config.UI_TEXT)

                self.screen.blit(rank_surface, (col_rank, y_offset))
                self.screen.blit(name_surface, (col_name, y_offset))
                self.screen.blit(score_surface, (col_score, y_offset))
                self.screen.blit(level_surface, (col_level, y_offset + 5))

                y_offset += row_height

        back_text = self.assets.fonts['medium'].render(
            "Press ESC to Return", True, color_config.UI_TEXT)
        back_rect = back_text.get_rect(
            center=(center_x, screen_h - int(screen_h * 0.07)))
        self.screen.blit(back_text, back_rect)

    def draw_waiting_for_players(self):
        """Draw a screen indicating the client is waiting for another player."""
        self.screen.fill(color_config.BLACK)
        self.draw_starfield()

        title_font = self.assets.fonts['large']
        text = "Waiting for Player 2 to join..."
        text_surface = title_font.render(text, True, color_config.WHITE)
        text_rect = text_surface.get_rect(center=(game_config.SCREEN_WIDTH // 2, game_config.SCREEN_HEIGHT // 2))
        self.screen.blit(text_surface, text_rect)

        # Display "Return to Main Menu" option
        menu_font = self.assets.fonts['medium']
        menu_text = "Press ESC to Return to Main Menu"
        menu_surface = menu_font.render(menu_text, True, color_config.YELLOW)
        menu_rect = menu_surface.get_rect(center=(game_config.SCREEN_WIDTH // 2, game_config.SCREEN_HEIGHT // 2 + 100))

        self.screen.blit(menu_surface, menu_rect)


    
    def run(self):
        """Main game loop"""
        if self.is_server:
            # Server doesn't have a GUI loop - it's handled separately
            logger.error("Server instance should not call run(). Use server.py instead.")
            return
        
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(game_config.FPS)
        
        pygame.quit()

    def _test_server_connection(self):
        """Test connection to the server with the current input values."""
        # Get host and port from input fields
        host = self.server_connect_input.text if self.server_connect_input else self.server_host
        port_str = self.server_port_input.text if self.server_port_input else str(self.server_port)
        
        try:
            port = int(port_str) if port_str else DEFAULT_SERVER_PORT
        except ValueError:
            self.server_test_result = "Invalid port number"
            self.server_test_result_timer = 180
            return
        
        # Use default if empty
        if not host:
            host = DEFAULT_SERVER_HOST
        
        # Run connection test in a blocking manner (small timeout)
        success, message = test_connection(host, port, timeout=3.0)
        self.server_test_result = message
        self.server_test_result_timer = 180  # 3 seconds at 60 FPS
        
        if success:
            # Update stored values on successful connection test
            self.server_host = host
            self.server_port = port
    
    def _connect_to_server_from_ui(self):
        """Connect to server using values from UI input fields."""
        # Get host and port from input fields
        host = self.server_connect_input.text if self.server_connect_input else self.server_host
        port_str = self.server_port_input.text if self.server_port_input else str(self.server_port)
        
        try:
            port = int(port_str) if port_str else DEFAULT_SERVER_PORT
        except ValueError:
            self.server_test_result = "Invalid port number"
            self.server_test_result_timer = 180
            return
        
        # Use default if empty
        if not host:
            host = DEFAULT_SERVER_HOST
        
        # Store the values
        self.server_host = host
        self.server_port = port
        
        # Attempt connection
        logger.info(f"Connecting to server at {host}:{port}...")
        if self.connect_to_server(host, port):
            logger.info("Connected to server. Initializing game...")
            self.init_game()
            self.state = GameState.WAITING_FOR_PLAYERS
        else:
            self.server_test_result = f"Failed to connect to {host}:{port}"
            self.server_test_result_timer = 180
    
    def _init_server_connect_inputs(self):
        """Initialize server connection input fields."""
        screen_w = game_config.SCREEN_WIDTH
        screen_h = game_config.SCREEN_HEIGHT
        box_width = min(500, screen_w - 40)
        box_x = (screen_w - box_width) // 2
        box_y = max(20, int(screen_h * 0.16))

        if not self.server_connect_input:
            self.server_connect_input = TextInput(
                box_x + 30, box_y + 70, box_width - 60, 50,
                self.assets.fonts['medium'], max_length=30, placeholder="Server Address"
            )
            self.server_connect_input.text = self.server_host

        if not self.server_port_input:
            self.server_port_input = TextInput(
                box_x + 30, box_y + 170, box_width - 60, 50,
                self.assets.fonts['medium'], max_length=5, placeholder="Port"
            )
            self.server_port_input.text = str(self.server_port)
    
    def draw_server_connect(self):
        """Draw the server connection screen."""
        screen_w = game_config.SCREEN_WIDTH
        screen_h = game_config.SCREEN_HEIGHT

        # Initialize inputs if needed
        self._init_server_connect_inputs()

        # Draw overlay
        overlay = pygame.Surface((screen_w, screen_h))
        overlay.fill(color_config.BLACK)
        overlay.set_alpha(220)
        self.screen.blit(overlay, (0, 0))

        # Draw title
        title = self.assets.fonts['large'].render("PLAY ONLINE", True, color_config.CYAN)
        title_rect = title.get_rect(center=(screen_w // 2, int(screen_h * 0.10)))
        self.screen.blit(title, title_rect)

        # Draw box
        box_width = min(500, screen_w - 40)
        box_height = min(450, screen_h - int(screen_h * 0.20))
        box_x = (screen_w - box_width) // 2
        box_y = max(20, int(screen_h * 0.16))

        pygame.draw.rect(self.screen, color_config.UI_BG, (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, color_config.CYAN, (box_x, box_y, box_width, box_height), 3)

        # Server Address
        addr_label = self.assets.fonts['medium'].render("Server Address:", True, color_config.WHITE)
        self.screen.blit(addr_label, (box_x + 30, box_y + 40))

        # Draw address input field
        self.server_connect_input.rect.x = box_x + 30
        self.server_connect_input.rect.y = box_y + 70
        self.server_connect_input.rect.width = box_width - 60
        self.server_connect_input.draw(self.screen)
        if self.server_selected_index == 0:
            pygame.draw.rect(self.screen, color_config.CYAN, self.server_connect_input.rect, 3, border_radius=10)

        # Server Port
        port_label = self.assets.fonts['medium'].render("Port:", True, color_config.WHITE)
        self.screen.blit(port_label, (box_x + 30, box_y + 140))

        # Draw port input field
        self.server_port_input.rect.x = box_x + 30
        self.server_port_input.rect.y = box_y + 170
        self.server_port_input.rect.width = box_width - 60
        self.server_port_input.draw(self.screen)
        if self.server_selected_index == 1:
            pygame.draw.rect(self.screen, color_config.CYAN, self.server_port_input.rect, 3, border_radius=10)

        if self.server_test_result and self.server_test_result_timer > 0:
            self.server_test_result_timer -= 1
            success = self.server_test_result.startswith("Connected")
            result_color = color_config.GREEN if success else color_config.RED
            result_text = self.assets.fonts['small'].render(self.server_test_result, True, result_color)
            result_rect = result_text.get_rect(center=(screen_w // 2, box_y + 230))
            self.screen.blit(result_text, result_rect)

        # Button dimensions
        button_width = max(100, int(box_width * 0.28))
        button_height = max(44, int(screen_h * 0.065))
        button_y = box_y + 280

        # Test Connection button
        test_btn_x = box_x + 30
        self.server_test_button_rect = pygame.Rect(test_btn_x, button_y, button_width, button_height)
        test_selected = (self.server_selected_index == 2)
        pygame.draw.rect(
            self.screen,
            (*color_config.YELLOW, 40) if test_selected else (*color_config.UI_BG, 160),
            self.server_test_button_rect,
            border_radius=12,
        )
        pygame.draw.rect(self.screen, color_config.YELLOW if test_selected else color_config.UI_BORDER, self.server_test_button_rect, 2, border_radius=12)
        test_text = self.assets.fonts['small'].render("TEST", True, color_config.WHITE)
        test_rect = test_text.get_rect(center=self.server_test_button_rect.center)
        self.screen.blit(test_text, test_rect)

        # Connect button
        connect_btn_x = box_x + box_width - button_width - 30
        self.server_connect_button_rect = pygame.Rect(connect_btn_x, button_y, button_width, button_height)
        connect_selected = (self.server_selected_index == 3)
        pygame.draw.rect(
            self.screen,
            (*color_config.GREEN, 40) if connect_selected else (*color_config.UI_BG, 160),
            self.server_connect_button_rect,
            border_radius=12,
        )
        pygame.draw.rect(self.screen, color_config.GREEN if connect_selected else color_config.UI_BORDER, self.server_connect_button_rect, 2, border_radius=12)
        connect_text = self.assets.fonts['small'].render("CONNECT", True, color_config.WHITE)
        connect_rect = connect_text.get_rect(center=self.server_connect_button_rect.center)
        self.screen.blit(connect_text, connect_rect)

        # Back button
        back_btn_x = box_x + (box_width - button_width) // 2
        self.server_back_button_rect = pygame.Rect(back_btn_x, button_y + button_height + 14, button_width, button_height)
        back_selected = (self.server_selected_index == 4)
        pygame.draw.rect(
            self.screen,
            (*color_config.CYAN, 40) if back_selected else (*color_config.UI_BG, 160),
            self.server_back_button_rect,
            border_radius=12,
        )
        pygame.draw.rect(self.screen, color_config.CYAN if back_selected else color_config.UI_BORDER, self.server_back_button_rect, 2, border_radius=12)
        back_text = self.assets.fonts['small'].render("BACK", True, color_config.WHITE)
        back_rect = back_text.get_rect(center=self.server_back_button_rect.center)
        self.screen.blit(back_text, back_rect)

        # Instructions
        instructions = self.assets.fonts['tiny'].render(
            "1: Address | 2: Port | 3: Test | 4: Connect | 5: Back | TAB: Next | ENTER: Select",
            True, color_config.UI_TEXT)
        instructions_rect = instructions.get_rect(center=(screen_w // 2, box_y + box_height - 20))
        self.screen.blit(instructions, instructions_rect)

    def _handle_menu_action(self, action: str):
        """Handle actions based on main menu selection."""
        if action == "play_online":  
            self._init_server_connect_inputs()
            self.server_selected_index = 0
            self.server_test_result = None
            self.state = GameState.SERVER_CONNECT
            return

        if action == "play":
            logger.info("Game started (via menu)")
            if self.next_level_pending:
                self.current_level += 1
                self.next_level_pending = False
            self.init_game()
            self.state = GameState.PLAYING
        elif action == "shop":
            logger.info("Shop opened (via menu)")
            
            if not self.player or self.player is None:
                self.player = Player(game_config.SCREEN_WIDTH // 2, game_config.SCREEN_HEIGHT - 100)
            
            if self.current_profile:
                self.player.coins = self.current_profile.coins
            self.state = GameState.SHOP
        elif action == "scores":
            logger.info("High scores viewed (via menu)")
            self.state = GameState.HIGH_SCORES
        elif action == "profile":
            logger.info("Profile selection (via menu)")
            self.state = GameState.PROFILE_SELECT
        elif action == "quit":
            logger.info("Quit selected from menu")
            self.state = GameState.QUIT_CONFIRM
            self.quit_confirm_context = 'game'
            self.quit_confirm_selected = False
