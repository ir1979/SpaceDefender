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
from ui import HUD, Shop, TextInput

logger = get_logger('space_defender.game')

class Level:
    """Level manager"""
    
    def __init__(self, level_num: int):
        self.level_num = level_num
        self.enemies_to_spawn = 30 + (level_num * 15)
        self.enemies_spawned = 0
        self.spawn_timer = 0
        self.spawn_delay = max(20, 60 - (level_num * 3))
        self.powerup_timer = 0
        self.powerup_delay = 300
        self.time_limit = game_config.LEVEL_TIME_LIMIT + (level_num * 10)
        self.time_remaining = self.time_limit
        self.start_time = time.time()
    
    def update_timer(self):
        elapsed = time.time() - self.start_time
        self.time_remaining = max(0, self.time_limit - elapsed)
        return self.time_remaining > 0
    
    def should_spawn_enemy(self) -> bool:
        if self.enemies_spawned < self.enemies_to_spawn:
            self.spawn_timer += 1
            if self.spawn_timer >= self.spawn_delay:
                self.spawn_timer = 0
                self.enemies_spawned += 1
                return True
        return False
    
    def should_spawn_powerup(self) -> bool:
        self.powerup_timer += 1
        if self.powerup_timer >= self.powerup_delay:
            self.powerup_timer = 0
            return random.random() < 0.3
        return False

class Game:
    """Main game controller"""
    def __init__(self, profile: PlayerProfile = None, is_server=False):
        """
        Initializes the Game. 
        :param is_server: If True, runs without GUI, Assets, or Sound.
        """
        self.is_server = is_server
        self.is_network_mode = False # Default to False, client will set to True
        self.player_id = None # Will be assigned by server during handshake
        self.running = True
        
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
        self.text_input = None
        self.quit_confirm_selected = True
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

    def _init_game(self):
        # In network mode, the client doesn't initialize the game, the server does.
        if self.is_network_mode:
            return

        """Legacy method for profile-based game initialization. Routes to init_game()."""
        if self.profile:
            self.current_profile = self.profile
        self.init_game()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return # Exit early
            
            # --- State-based Event Handling ---
            
            if self.state == GameState.SPLASH_SCREEN:
                if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                    if self.splash_ready:
                        # Go to PROFILE_SELECT to choose existing profile or create new
                        self.state = GameState.PROFILE_SELECT
                        self.splash_skipped = True
            
            elif self.state == GameState.NAME_INPUT:
                if self.text_input:
                    result = self.text_input.handle_event(event)
                    if result:
                        profile_name = result.strip()
                        if profile_name:
                            if SaveSystem.profile_exists(profile_name):
                                self.duplicate_profile_error = True
                                self.duplicate_error_timer = 180 # 3 seconds at 60 FPS
                            else:
                                # Store the new profile name and transition to password input
                                self.new_profile_name = profile_name
                                self.state = GameState.PASSWORD_INPUT
                                self.authenticating_profile = profile_name  # Reuse field for display
                                self.password_input = TextInput(
                                    game_config.SCREEN_WIDTH // 2 - 150, 350, 300, 60,
                                    self.assets.fonts['medium'], is_password=True)
                        else:
                            self.duplicate_profile_error = True
                            self.duplicate_error_timer = 180
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        # Cancel profile creation, go back to profile select
                        self.state = GameState.PROFILE_SELECT
                        self.creating_new_profile = False
            
            if self.state == GameState.PROFILE_SELECT:
                if event.type == pygame.KEYDOWN:
                    if self.server_socket:
                        try:
                            self.server_socket.close()
                        except Exception: pass
                    if event.key == pygame.K_ESCAPE:
                        # ESC allows users to create a new profile instead of selecting existing
                        self.creating_new_profile = True
                        self.state = GameState.NAME_INPUT
                        self.text_input = TextInput(
                            game_config.SCREEN_WIDTH // 2 - 200, 350, 400, 60,
                            self.assets.fonts['medium'])
                    elif event.key == pygame.K_n:
                        self.creating_new_profile = True
                        self.state = GameState.NAME_INPUT
                        self.text_input = TextInput(
                            game_config.SCREEN_WIDTH // 2 - 200, 350, 400, 60,
                            self.assets.fonts['medium'])
                    elif event.unicode.isdigit():
                        idx = int(event.unicode) - 1
                        profiles = SaveSystem.get_profiles()
                        if 0 <= idx < len(profiles):
                            # Transition to PASSWORD_INPUT state for authentication
                            self.authenticating_profile = profiles[idx].name
                            self.state = GameState.PASSWORD_INPUT
                            self.password_input = TextInput(
                                game_config.SCREEN_WIDTH // 2 - 150, 350, 300, 60,
                                self.assets.fonts['medium'], is_password=True)
                            self.password_error = False
                    elif event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                        profiles = SaveSystem.get_profiles()
                        if profiles:
                            idx = self.profile_selected_index
                            if 0 <= idx < len(profiles):
                                self._delete_profile_at_index(idx)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for box_rect, idx in self.profile_buttons:
                        if box_rect.collidepoint(event.pos):
                            profiles = SaveSystem.get_profiles()
                            if 0 <= idx < len(profiles):
                                # Transition to PASSWORD_INPUT state for authentication
                                self.authenticating_profile = profiles[idx].name
                                self.state = GameState.PASSWORD_INPUT
                                self.password_input = TextInput(
                                    game_config.SCREEN_WIDTH // 2 - 150, 350, 300, 60,
                                    self.assets.fonts['medium'], is_password=True)
                                self.password_error = False
                                break
                    if self.new_profile_button and self.new_profile_button.collidepoint(event.pos):
                        self.creating_new_profile = True
                        self.state = GameState.NAME_INPUT
                        self.text_input = TextInput(
                            game_config.SCREEN_WIDTH // 2 - 200, 350, 400, 60,
                            self.assets.fonts['medium'])
                
                elif event.type == pygame.MOUSEMOTION:
                    for box_rect, idx in self.profile_buttons:
                        if box_rect.collidepoint(event.pos):
                            self.profile_selected_index = idx
                            break
            
            elif self.state == GameState.PASSWORD_INPUT:
                if self.password_input:
                    result = self.password_input.handle_event(event)
                    if result:
                        password = result.strip()
                        # Check if this is creating a new profile or authenticating
                        if self.new_profile_name:
                            # Creating new profile
                            self.profile = PlayerProfile(self.new_profile_name, password)
                            SaveSystem.save_profile(self.profile)
                            self._apply_profile_start_level(self.profile)
                            self.new_profile_name = None
                            self.state = GameState.MAIN_MENU
                        else:
                            # Authenticating existing profile
                            if SaveSystem.verify_password(self.authenticating_profile, password):
                                profile = SaveSystem.load_profile(self.authenticating_profile)
                                self.profile = profile
                                self._apply_profile_start_level(profile)
                                self.state = GameState.MAIN_MENU
                            else:
                                # Password incorrect
                                self.password_error = True
                                self.password_error_timer = 180  # 3 seconds at 60 FPS
                                self.password_input = TextInput(
                                    game_config.SCREEN_WIDTH // 2 - 150, 350, 300, 60,
                                    self.assets.fonts['medium'], is_password=True)
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        # Cancel password input
                        if self.new_profile_name:
                            # Cancel new profile creation, go back to name input
                            self.new_profile_name = None
                            self.state = GameState.NAME_INPUT
                            self.text_input = TextInput(
                                game_config.SCREEN_WIDTH // 2 - 200, 350, 400, 60,
                                self.assets.fonts['medium'])
                        else:
                            # Cancel authentication, go back to profile select
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
                        self.running = False
                elif event.type == pygame.MOUSEMOTION:
                    mouse_pos = event.pos
                    for i, (button_rect, action) in enumerate(self.menu_buttons):
                        if button_rect.collidepoint(mouse_pos):
                            self.menu_selected_index = i
                            break
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.menu_buttons:
                        _, action = self.menu_buttons[self.menu_selected_index]
                        self._handle_menu_action(action)

            elif self.state == GameState.PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_q, pygame.K_ESCAPE]:
                        self.state = GameState.QUIT_CONFIRM
                        self.quit_confirm_selected = True # Default to YES
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
                                    break
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
                                    score = int(enemy.max_health * 10)
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
                                    break
                                # Use the enemy freeze (decrement count)
                                self.player.use_weapon('enemy_freeze')
                                
                                logger.info("❄️ ENEMY FREEZE ACTIVATED! Freezing all enemies!")
                                self.assets.play_sound('powerup', 0.7)
                                for enemy in self.enemies:
                                    if not hasattr(enemy, 'frozen_timer'):
                                        enemy.frozen_timer = 0
                                    enemy.frozen_timer = 300  # 5 seconds at 60 FPS
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
                    # We must only save if a purchase was actually made.
                    if self.current_profile and self.player and self.player.coins != self.current_profile.total_coins:
                        logger.info(f"Shop closed with a change in coins. "
                                    f"Old: {self.current_profile.total_coins}, New: {self.player.coins}. Saving profile.")
                        self.current_profile.sync_after_shop(self.player.coins) # Sync and save
                        SaveSystem.save_profile(self.current_profile)
                    else:
                        logger.info("Shop closed without any purchase. No save needed.")
                    self.state = GameState.MAIN_MENU

            elif self.state == GameState.QUIT_CONFIRM:
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_LEFT, pygame.K_a]:
                        self.quit_confirm_selected = False # Select NO
                    elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                        self.quit_confirm_selected = True # Select YES
                    elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                        if self.quit_confirm_selected: # YES
                            # Player chose to quit the level. We should end the game session
                            # but not penalize their total accumulated coins.
                            # The correct way to do this is to simply reload the profile,
                            # discarding any transient changes from the aborted game.
                            if self.current_profile:
                                self.current_profile = SaveSystem.load_profile(self.current_profile.name)
                            self.all_sprites.empty()
                            self.state = GameState.MAIN_MENU
                        else: # NO
                            self.state = GameState.PLAYING
                    elif event.key == pygame.K_ESCAPE:
                        self.state = GameState.PLAYING # Cancel
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.quit_yes_rect and self.quit_yes_rect.collidepoint(event.pos):
                        # Player chose to quit the level.
                        if self.current_profile:
                            self.current_profile = SaveSystem.load_profile(self.current_profile.name)
                        self.all_sprites.empty()
                        self.state = GameState.MAIN_MENU
                    elif self.quit_no_rect and self.quit_no_rect.collidepoint(event.pos):
                        self.state = GameState.PLAYING

            elif self.state == GameState.SERVER_CONNECT:
                if event.type == pygame.KEYDOWN:
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
                    elif event.key == pygame.K_BACKSPACE:
                        # Handle backspace for input fields
                        if self.server_selected_index == 0 and self.server_connect_input:
                            self.server_connect_input.text = self.server_connect_input.text[:-1]
                        elif self.server_selected_index == 1 and self.server_port_input:
                            self.server_port_input.text = self.server_port_input.text[:-1]
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
                elif event.type == pygame.KEYDOWN:
                    # Handle text input for selected field
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
            if y > game_config.SCREEN_HEIGHT:
                y = 0
                x = random.randint(0, game_config.SCREEN_WIDTH)
            self.stars[i] = (x, y, size)
    
    def draw_starfield(self):
        for x, y, size in self.stars:
            brightness = 100 + (size * 50)
            color = (brightness, brightness, brightness)
            pygame.draw.circle(self.screen, color, (int(x), int(y)), size)
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
            
            self.all_sprites.add(self.player)

        self.level = Level(self.current_level)
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
                e = EnemyFactory.create(etype, ex, ey, 1)
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
                bullet = BulletFactory.create(weapon, bx, by, speed, damage, angle)
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
                    self.assets.fonts['medium'])
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
            
            # Update timer
            if not self.level.update_timer():
                if self.current_profile:
                    coins_earned = self.player.coins - self.current_profile.session_start_coins
                    session_time = time.time() - self.session_start_time
                    self.current_profile.end_game(
                        self.player.score,
                        coins_earned,
                        self.current_level,
                        session_time
                    )
                    SaveSystem.save_profile(self.current_profile)
                    SaveSystem.save_high_score(
                        self.current_profile,
                        self.player.score,
                        self.current_level
                    )
                self.state = GameState.GAME_OVER
                return
            
            # Update sprites
            self.all_sprites.update()
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
            
            # Spawn enemies
            if self.level.should_spawn_enemy():
                enemy_type = EnemyFactory.get_random_type(self.current_level)
                enemy = EnemyFactory.create(
                    enemy_type, 
                    random.randint(50, game_config.SCREEN_WIDTH - 50),
                    -50, # y-position
                    self.current_level
                )
                if enemy:
                    self.enemies.add(enemy)
                    self.all_sprites.add(enemy)
            
            # Spawn power-ups
            if self.level.should_spawn_powerup():
                power_type = random.choice(['rapid_fire', 'shield', 'triple_shot', 'health'])
                powerup = PowerUp(
                    random.randint(50, game_config.SCREEN_WIDTH - 50),
                    -30,
                    power_type
                )
                self.powerups.add(powerup)
                self.all_sprites.add(powerup)
            
            # Check bullet-enemy collisions
            for bullet in self.bullets:
                hit_enemies = pygame.sprite.spritecollide(bullet, self.enemies, False)
                if hit_enemies:
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
                            score_gained = enemy.score_value
                            # On server, update players[0]; on client, update self.player
                            if self.is_server and self.players:
                                self.players[0].coins += coins_gained
                                self.players[0].score += score_gained
                            elif not self.is_server and self.player:
                                self.player.coins += coins_gained
                                self.player.score += score_gained
                            logger.debug(f"Enemy destroyed. Player gained {coins_gained} coins, {score_gained} score.")
                            enemy.kill()
                        else:
                            if not self.is_server:
                                self.particle_system.emit_explosion(
                                    bullet.rect.centerx, bullet.rect.centery,
                                    color_config.ORANGE, 10)
            
            # --- Player Collision Logic ---
            # This logic needs to handle both a single local player and multiple server-side players.
            players_to_check = self.players if self.is_server else ([self.player] if self.player else [])

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
                            self.game_state_from_server.get('time_remaining', 0)
                        )
                    else:
                        # Before first server state arrives: show placeholder HUD
                        if self.player:
                            time_remaining = self.level.time_remaining if self.level else 0
                            self.hud.draw(self.screen, self.player, self.current_level, time_remaining)
                else:
                    # Local single-player HUD
                    time_remaining = self.level.time_remaining if self.level else 0
                    self.hud.draw(self.screen, self.player, self.current_level, time_remaining)
        
        elif self.state == GameState.PAUSED:
            if self.player:
                self.all_sprites.draw(self.screen)
                self.draw_pause_screen()
        
        elif self.state == GameState.SHOP:
            if self.player:
                self.all_sprites.draw(self.screen)
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
        """Draw name input screen for creating a new profile"""
        screen_w = game_config.SCREEN_WIDTH
        screen_h = game_config.SCREEN_HEIGHT
        
        # Draw title
        title = self.assets.fonts['large'].render("CREATE NEW PROFILE", True, color_config.GREEN)
        title_rect = title.get_rect(center=(screen_w // 2, 150))
        self.screen.blit(title, title_rect)
        
        # Explanation
        explanation = self.assets.fonts['medium'].render(
            "Enter a unique username for your new profile",
            True, color_config.WHITE)
        explanation_rect = explanation.get_rect(center=(screen_w // 2, 220))
        self.screen.blit(explanation, explanation_rect)
        
        # Username label
        username_label = self.assets.fonts['medium'].render("Username:", True, color_config.UI_TEXT)
        username_label_rect = username_label.get_rect(topleft=(screen_w // 2 - 200, 280))
        self.screen.blit(username_label, username_label_rect)
        
        # Password input field
        if self.text_input:
            self.text_input.draw(self.screen)
        
        # Display duplicate profile error message if active
        if self.duplicate_profile_error:
            # Note: timer is already decremented in update() — do NOT decrement here again
            error_text = self.assets.fonts['medium'].render(
                "❌ Username already exists! Please choose a different one.",
                True, color_config.RED)
            error_rect = error_text.get_rect(center=(screen_w // 2, 380))
            self.screen.blit(error_text, error_rect)
        
        # Detailed instructions
        hint1 = self.assets.fonts['small'].render(
            "After entering username, you'll be asked to set a password",
            True, color_config.UI_TEXT)
        hint1_rect = hint1.get_rect(center=(screen_w // 2, 440))
        self.screen.blit(hint1, hint1_rect)
        
        hint2 = self.assets.fonts['small'].render(
            "Press ENTER to continue • ESC to cancel",
            True, color_config.UI_TEXT)
        hint2_rect = hint2.get_rect(center=(screen_w // 2, 470))
        self.screen.blit(hint2, hint2_rect)
    
    def draw_profile_select(self):
        """Draw profile selection screen (centered & responsive)"""
        screen_w = game_config.SCREEN_WIDTH
        screen_h = game_config.SCREEN_HEIGHT
        margin = 20

        title = self.assets.fonts['large'].render("SELECT PROFILE", True, color_config.CYAN)
        title_rect = title.get_rect(center=(screen_w // 2, int(screen_h * 0.08)))
        self.screen.blit(title, title_rect)
        
        # Subtitle explaining the options
        subtitle = self.assets.fonts['small'].render(
            "Click a profile to authenticate with password • N or ESC to create new profile",
            True, color_config.UI_TEXT)
        subtitle_rect = subtitle.get_rect(center=(screen_w // 2, int(screen_h * 0.14)))
        self.screen.blit(subtitle, subtitle_rect)
        
        profiles = SaveSystem.get_profiles()
        box_width = min(700, screen_w - 400)
        box_height = 80
        x = (screen_w - box_width) // 2
        y_offset = int(screen_h * 0.22)
        mouse_pos = pygame.mouse.get_pos()
        
        # Clear and rebuild profile button list
        self.profile_buttons = []
        
        for i, profile in enumerate(profiles[:5]):
            box_rect = pygame.Rect(x, y_offset, box_width, box_height)
            self.profile_buttons.append((box_rect, i))
            
            # Check if mouse is hovering over this profile and update selection
            if box_rect.collidepoint(mouse_pos):
                self.profile_selected_index = i
            
            is_selected = (i == self.profile_selected_index)
            
            # Draw background with highlight if selected
            if is_selected:
                pygame.draw.rect(self.screen, color_config.CYAN, box_rect)
                pygame.draw.rect(self.screen, color_config.WHITE, box_rect, 3)
            else:
                pygame.draw.rect(self.screen, color_config.UI_BG, box_rect)
                pygame.draw.rect(self.screen, color_config.UI_BORDER, box_rect, 2)
            
            # Text positions inside box
            text_pad = 20
            num_text = f"{i + 1}."
            num_surface = self.assets.fonts['medium'].render(num_text, True, (color_config.BLACK if is_selected else color_config.YELLOW))
            self.screen.blit(num_surface, (x + text_pad, y_offset + 10))
            
            name_surface = self.assets.fonts['medium'].render(profile.name, True, (color_config.BLACK if is_selected else color_config.WHITE))
            self.screen.blit(name_surface, (x + text_pad + 60, y_offset + 10))
            
            stats_text = f"Lvl {profile.highest_level} | Score: {profile.total_score} | Coins: {profile.total_coins}"
            stats_surface = self.assets.fonts['small'].render(stats_text, True, (color_config.BLACK if is_selected else color_config.UI_TEXT))
            self.screen.blit(stats_surface, (x + text_pad + 60, y_offset + 45))
            
            y_offset += box_height + 20
        
        # New Profile button - centered under the boxes
        new_profile_rect = pygame.Rect(x, y_offset + 10, box_width, 60)
        self.new_profile_button = new_profile_rect
        new_hovered = new_profile_rect.collidepoint(mouse_pos)
        
        if new_hovered:
            pygame.draw.rect(self.screen, color_config.GREEN, new_profile_rect)
            pygame.draw.rect(self.screen, color_config.WHITE, new_profile_rect, 3)
            new_profile_color = color_config.BLACK
        else:
            pygame.draw.rect(self.screen, color_config.UI_BG, new_profile_rect)
            pygame.draw.rect(self.screen, color_config.GREEN, new_profile_rect, 2)
            new_profile_color = color_config.GREEN
        
        new_profile = self.assets.fonts['medium'].render("N or ESC - Create New Profile", True, new_profile_color)
        new_rect = new_profile.get_rect(center=new_profile_rect.center)
        self.screen.blit(new_profile, new_rect)
        
        hint = self.assets.fonts['small'].render(
            "Select with mouse or keyboard (1-5) • Existing profiles require password authentication",
            True, color_config.UI_TEXT)
        hint_rect = hint.get_rect(center=(screen_w // 2, y_offset + 110))
        self.screen.blit(hint, hint_rect)
    
    def draw_password_input(self):
        """Draw password input screen with clear distinction between authentication and creation"""
        screen_w = game_config.SCREEN_WIDTH
        screen_h = game_config.SCREEN_HEIGHT
        
        # Determine if creating new profile or authenticating existing
        is_creating = bool(self.new_profile_name)
        
        # Draw overlay
        overlay = pygame.Surface((screen_w, screen_h))
        overlay.fill(color_config.BLACK)
        overlay.set_alpha(220)
        self.screen.blit(overlay, (0, 0))
        
        # Draw dialog box - larger for new profile, normal for authentication
        box_width = 600 if is_creating else 550
        box_height = 400 if is_creating else 360
        box_x = (screen_w - box_width) // 2
        box_y = (screen_h - box_height) // 2
        
        # Color coding based on state
        border_color = color_config.GREEN if is_creating else color_config.CYAN
        
        pygame.draw.rect(self.screen, color_config.UI_BG, (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, border_color, (box_x, box_y, box_width, box_height), 4)
        
        # ===== CREATING NEW PROFILE =====
        if is_creating:
            # Title with color emphasis
            title = self.assets.fonts['large'].render("CREATE NEW PROFILE", True, color_config.GREEN)
            title_rect = title.get_rect(center=(screen_w // 2, box_y + 30))
            self.screen.blit(title, title_rect)
            
            # Large explanatory text
            explanation = self.assets.fonts['medium'].render(
                "This username is new. Set a password to protect your profile.",
                True, color_config.WHITE)
            explanation_rect = explanation.get_rect(center=(screen_w // 2, box_y + 85))
            self.screen.blit(explanation, explanation_rect)
            
            # Username display
            username_label = self.assets.fonts['small'].render("Username:", True, color_config.UI_TEXT)
            username_label_rect = username_label.get_rect(topleft=(box_x + 40, box_y + 140))
            self.screen.blit(username_label, username_label_rect)
            
            username_value = self.assets.fonts['medium'].render(
                self.new_profile_name, True, color_config.GREEN)
            username_value_rect = username_value.get_rect(topleft=(box_x + 40, box_y + 165))
            self.screen.blit(username_value, username_value_rect)
            
            # Password field label
            pwd_label = self.assets.fonts['medium'].render("Set Password:", True, color_config.WHITE)
            pwd_label_rect = pwd_label.get_rect(topleft=(box_x + 40, box_y + 220))
            self.screen.blit(pwd_label, pwd_label_rect)
            
            # Instructions
            instructions = self.assets.fonts['small'].render(
                "Choose a password to secure your profile • Press ENTER to confirm • ESC to cancel",
                True, color_config.UI_TEXT)
            instructions_rect = instructions.get_rect(center=(screen_w // 2, box_y + 360))
            self.screen.blit(instructions, instructions_rect)
        
        # ===== AUTHENTICATING EXISTING PROFILE =====
        else:
            # Title with color emphasis
            title = self.assets.fonts['large'].render("AUTHENTICATE PROFILE", True, color_config.CYAN)
            title_rect = title.get_rect(center=(screen_w // 2, box_y + 30))
            self.screen.blit(title, title_rect)
            
            # Large explanatory text
            explanation = self.assets.fonts['medium'].render(
                "This profile already exists. Enter your password to access it.",
                True, color_config.WHITE)
            explanation_rect = explanation.get_rect(center=(screen_w // 2, box_y + 85))
            self.screen.blit(explanation, explanation_rect)
            
            # Username display
            username_label = self.assets.fonts['small'].render("Profile:", True, color_config.UI_TEXT)
            username_label_rect = username_label.get_rect(topleft=(box_x + 40, box_y + 140))
            self.screen.blit(username_label, username_label_rect)
            
            username_value = self.assets.fonts['medium'].render(
                self.authenticating_profile, True, color_config.CYAN)
            username_value_rect = username_value.get_rect(topleft=(box_x + 40, box_y + 165))
            self.screen.blit(username_value, username_value_rect)
            
            # Password field label
            pwd_label = self.assets.fonts['medium'].render("Password:", True, color_config.WHITE)
            pwd_label_rect = pwd_label.get_rect(topleft=(box_x + 40, box_y + 220))
            self.screen.blit(pwd_label, pwd_label_rect)
            
            # Instructions
            instructions = self.assets.fonts['small'].render(
                "Enter your password • Press ENTER to submit • ESC to cancel",
                True, color_config.UI_TEXT)
            instructions_rect = instructions.get_rect(center=(screen_w // 2, box_y + 320))
            self.screen.blit(instructions, instructions_rect)
        
        # Password input field (common for both states)
        if self.password_input:
            self.password_input.update()
            # Adjust position based on state
            pwd_input_y = box_y + 250 if is_creating else box_y + 245
            original_y = self.password_input.rect.y
            self.password_input.rect.y = pwd_input_y
            self.password_input.draw(self.screen)
            self.password_input.rect.y = original_y
        
        # Error message with timeout
        if self.password_error:
            self.password_error_timer -= 1
            if self.password_error_timer <= 0:
                self.password_error = False
            else:
                # Blinking effect for error message
                if self.password_error_timer % 30 > 15:
                    error_msg = self.assets.fonts['medium'].render(
                        "❌ INCORRECT PASSWORD - Try again or press ESC to go back",
                        True, color_config.RED)
                    error_y = box_y + 310 if is_creating else box_y + 280
                    error_rect = error_msg.get_rect(center=(screen_w // 2, error_y))
                    self.screen.blit(error_msg, error_rect)
    
    def draw_main_menu(self):
        """Draw main menu (responsive layout)"""
        screen_w = game_config.SCREEN_WIDTH
        screen_h = game_config.SCREEN_HEIGHT
        title_y = int(screen_h * 0.14)

        title = self.assets.fonts['title'].render("SPACE DEFENDER", True, color_config.CYAN)
        title_rect = title.get_rect(center=(screen_w // 2, title_y))
        self.screen.blit(title, title_rect)

        if self.current_profile:
            welcome = self.assets.fonts['medium'].render(
                f"Welcome, {self.current_profile.name}!", True, color_config.GREEN)
            welcome_rect = welcome.get_rect(center=(screen_w // 2, title_y + 80))
            self.screen.blit(welcome, welcome_rect)

            stats_text = f"Total Score: {self.current_profile.total_score} | " \
                        f"Total Coins: {self.current_profile.total_coins} | " \
                        f"Best Level: {self.current_profile.highest_level}"
            stats = self.assets.fonts['small'].render(stats_text, True, color_config.UI_TEXT)
            stats_rect = stats.get_rect(center=(screen_w // 2, title_y + 120))
            self.screen.blit(stats, stats_rect)

        # Menu layout
        mouse_pos = pygame.mouse.get_pos()
        start_y = int(screen_h * 0.45)
        spacing = int(screen_h * 0.06)
        options = [
            ("PRESS ENTER TO START", pygame.K_RETURN, "play"),
        ]
        
        # Add "PLAY ONLINE" option if server connection details are provided
        if self.server_host and self.server_port:
            options.append(("O - PLAY ONLINE", pygame.K_o, "play_online"))
        
        options.extend([
            ("S - SHOP", pygame.K_s, "shop"),
            ("H - HIGH SCORES", pygame.K_h, "scores"),
            ("P - CHANGE PROFILE", pygame.K_p, "profile"),
            ("ESC - QUIT", pygame.K_ESCAPE, "quit")
        ])

        # Store button rects for mouse detection
        self.menu_buttons = []
        button_width = min(520, screen_w - 300)
        button_height = 56

        for idx, (text, key, action) in enumerate(options):
            y = start_y + idx * spacing
            button_rect = pygame.Rect(
                screen_w // 2 - button_width // 2,
                y - button_height // 2,
                button_width,
                button_height
            )

            is_selected = (idx == self.menu_selected_index)
            if is_selected:
                pygame.draw.rect(self.screen, color_config.CYAN, button_rect)
                surface = self.assets.fonts['medium'].render(text, True, color_config.BLACK)
            else:
                surface = self.assets.fonts['medium'].render(text, True, color_config.WHITE)

            rect = surface.get_rect(center=button_rect.center)
            self.screen.blit(surface, rect)
            self.menu_buttons.append((button_rect, action))
    
    def draw_pause_screen(self):
        """Draw pause overlay"""
        overlay = pygame.Surface((game_config.SCREEN_WIDTH, game_config.SCREEN_HEIGHT))
        overlay.fill(color_config.BLACK)
        overlay.set_alpha(150)
        self.screen.blit(overlay, (0, 0))
        
        paused_text = self.assets.fonts['title'].render("PAUSED", True, color_config.CYAN)
        paused_rect = paused_text.get_rect(center=(game_config.SCREEN_WIDTH // 2, 300))
        self.screen.blit(paused_text, paused_rect)
        
        continue_text = self.assets.fonts['medium'].render(
            "Press P to Continue", True, color_config.WHITE)
        continue_rect = continue_text.get_rect(center=(game_config.SCREEN_WIDTH // 2, 400))
        self.screen.blit(continue_text, continue_rect)
    
    def draw_quit_confirm(self):
        """Draw quit confirmation dialog with warning and Yes/No buttons"""
        overlay = pygame.Surface((game_config.SCREEN_WIDTH, game_config.SCREEN_HEIGHT))
        overlay.fill(color_config.BLACK)
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title_text = self.assets.fonts['title'].render("QUIT GAME?", True, color_config.RED)
        title_rect = title_text.get_rect(center=(game_config.SCREEN_WIDTH // 2, 200))
        self.screen.blit(title_text, title_rect)
        
        # Warning message - updated to be more accurate
        warning = self.assets.fonts['medium'].render(
            "Progress from this session will be lost!", True, color_config.YELLOW)
        warning_rect = warning.get_rect(center=(game_config.SCREEN_WIDTH // 2, 280))
        self.screen.blit(warning, warning_rect)
        
        # Button dimensions
        button_width = 120
        button_height = 50
        button_y = 380
        button_spacing = 150
        
        yes_x = game_config.SCREEN_WIDTH // 2 - button_spacing
        no_x = game_config.SCREEN_WIDTH // 2 + button_spacing
        
        # Store button rects for mouse click handling
        self.quit_yes_rect = pygame.Rect(yes_x - button_width // 2, button_y - button_height // 2,
                                         button_width, button_height)
        self.quit_no_rect = pygame.Rect(no_x - button_width // 2, button_y - button_height // 2,
                                        button_width, button_height)
        
        # Draw buttons with selection highlight
        yes_color = color_config.GREEN if self.quit_confirm_selected else (60, 60, 60)
        no_color = color_config.RED if not self.quit_confirm_selected else (60, 60, 60)
        
        # Yes button
        pygame.draw.rect(self.screen, yes_color, self.quit_yes_rect)
        pygame.draw.rect(self.screen, color_config.WHITE, self.quit_yes_rect, 2)
        yes_text = self.assets.fonts['medium'].render("YES", True, color_config.WHITE)
        yes_text_rect = yes_text.get_rect(center=self.quit_yes_rect.center)
        self.screen.blit(yes_text, yes_text_rect)
        
        # No button
        pygame.draw.rect(self.screen, no_color, self.quit_no_rect)
        pygame.draw.rect(self.screen, color_config.WHITE, self.quit_no_rect, 2)
        no_text = self.assets.fonts['medium'].render("NO", True, color_config.WHITE)
        no_text_rect = no_text.get_rect(center=self.quit_no_rect.center)
        self.screen.blit(no_text, no_text_rect)
        
        # Instructions
        instructions = self.assets.fonts['small'].render(
            "LEFT/A: No  |  RIGHT/D: Yes  |  ENTER: Confirm  |  ESC: Cancel", 
            True, color_config.CYAN)
        instructions_rect = instructions.get_rect(center=(game_config.SCREEN_WIDTH // 2, 470))
        self.screen.blit(instructions, instructions_rect)
    
    def draw_level_complete(self):
        """Draw level complete screen"""
        self.screen.fill(color_config.BLACK)
        self.draw_starfield()
        
        title = self.assets.fonts['large'].render(
            f"LEVEL {self.current_level} COMPLETE!", True, color_config.GREEN)
        title_rect = title.get_rect(center=(game_config.SCREEN_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)
        
        time_bonus = int(self.level.time_remaining * 10)
        time_text = self.assets.fonts['medium'].render(
            f"Time Bonus: {time_bonus} points", True, color_config.CYAN)
        time_rect = time_text.get_rect(center=(game_config.SCREEN_WIDTH // 2, 280))
        self.screen.blit(time_text, time_rect)
        
        bonus = self.assets.fonts['medium'].render(
            f"Coin Bonus: {game_config.LEVEL_COIN_BONUS} Coins", True, color_config.YELLOW)
        bonus_rect = bonus.get_rect(center=(game_config.SCREEN_WIDTH // 2, 340))
        self.screen.blit(bonus, bonus_rect)
        
        score = self.assets.fonts['medium'].render(
            f"Total Score: {self.player.score}", True, color_config.WHITE)
        score_rect = score.get_rect(center=(game_config.SCREEN_WIDTH // 2, 400))
        self.screen.blit(score, score_rect)
        
        continue_text = self.assets.fonts['medium'].render(
            "Press ENTER to Continue or ESC for Menu", True, color_config.CYAN)
        continue_rect = continue_text.get_rect(center=(game_config.SCREEN_WIDTH // 2, 500))
        self.screen.blit(continue_text, continue_rect)
    
    def draw_game_over(self):
        """Draw game over screen"""
        self.screen.fill(color_config.BLACK)
        self.draw_starfield()
        
        title = self.assets.fonts['title'].render("GAME OVER", True, color_config.RED)
        title_rect = title.get_rect(center=(game_config.SCREEN_WIDTH // 2, 180))
        self.screen.blit(title, title_rect)
        
        if self.current_profile:
            name_text = self.assets.fonts['medium'].render(
                self.current_profile.name, True, color_config.CYAN)
            name_rect = name_text.get_rect(center=(game_config.SCREEN_WIDTH // 2, 260))
            self.screen.blit(name_text, name_rect)
        
        final_score = self.assets.fonts['large'].render(
            f"Final Score: {self.player.score}", True, color_config.WHITE)
        score_rect = final_score.get_rect(center=(game_config.SCREEN_WIDTH // 2, 320))
        self.screen.blit(final_score, score_rect)
        
        coins_text = self.assets.fonts['medium'].render(
            f"Total Coins Earned: {self.player.coins}", True, color_config.YELLOW)
        coins_rect = coins_text.get_rect(center=(game_config.SCREEN_WIDTH // 2, 390))
        self.screen.blit(coins_text, coins_rect)
        
        level_text = self.assets.fonts['medium'].render(
            f"Reached Level: {self.current_level}", True, color_config.CYAN)
        level_rect = level_text.get_rect(center=(game_config.SCREEN_WIDTH // 2, 450))
        self.screen.blit(level_text, level_rect)
        
        continue_text = self.assets.fonts['medium'].render(
            "Press ENTER or ESC to Return to Menu", True, color_config.WHITE)
        continue_rect = continue_text.get_rect(center=(game_config.SCREEN_WIDTH // 2, 550))
        self.screen.blit(continue_text, continue_rect)
    
    def draw_high_scores(self):
        """Draw high scores screen"""
        self.screen.fill(color_config.BLACK)
        self.draw_starfield()
        
        title = self.assets.fonts['title'].render("HIGH SCORES", True, color_config.CYAN)
        title_rect = title.get_rect(center=(game_config.SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        scores = SaveSystem.get_high_scores()
        
        if not scores:
            no_scores = self.assets.fonts['medium'].render(
                "No high scores yet!", True, color_config.WHITE)
            no_scores_rect = no_scores.get_rect(center=(game_config.SCREEN_WIDTH // 2, 300))
            self.screen.blit(no_scores, no_scores_rect)
        else:
            y_offset = 200
            for i, entry in enumerate(scores[:5]):
                rank_text = f"{i + 1}."
                name_text = entry['name']
                score_text = f"Score: {entry['score']}"
                level_text = f"Level: {entry['level']}"
                
                rank_surface = self.assets.fonts['medium'].render(rank_text, True, color_config.YELLOW)
                name_surface = self.assets.fonts['medium'].render(name_text, True, color_config.CYAN)
                score_surface = self.assets.fonts['medium'].render(score_text, True, color_config.WHITE)
                level_surface = self.assets.fonts['small'].render(level_text, True, color_config.UI_TEXT)
                
                self.screen.blit(rank_surface, (150, y_offset))
                self.screen.blit(name_surface, (220, y_offset))
                self.screen.blit(score_surface, (450, y_offset))
                self.screen.blit(level_surface, (680, y_offset + 5))
                
                y_offset += 50
        
        back_text = self.assets.fonts['medium'].render(
            "Press ESC to Return", True, color_config.UI_TEXT)
        back_rect = back_text.get_rect(
            center=(game_config.SCREEN_WIDTH // 2, game_config.SCREEN_HEIGHT - 50))
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
            self.state = GameState.PLAYING
            self.state = GameState.WAITING_FOR_PLAYERS
        else:
            self.server_test_result = f"Failed to connect to {host}:{port}"
            self.server_test_result_timer = 180
    
    def _init_server_connect_inputs(self):
        """Initialize server connection input fields."""
        if not self.server_connect_input:
            self.server_connect_input = TextInput(
                game_config.SCREEN_WIDTH // 2 - 150, 280, 300, 50,
                self.assets.fonts['medium'], max_length=30
            )
            self.server_connect_input.text = self.server_host
        
        if not self.server_port_input:
            self.server_port_input = TextInput(
                game_config.SCREEN_WIDTH // 2 - 75, 360, 150, 50,
                self.assets.fonts['medium'], max_length=5
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
        title_rect = title.get_rect(center=(screen_w // 2, 80))
        self.screen.blit(title, title_rect)
        
        # Draw box
        box_width = 500
        box_height = 450
        box_x = (screen_w - box_width) // 2
        box_y = 120
        
        pygame.draw.rect(self.screen, color_config.UI_BG, (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, color_config.CYAN, (box_x, box_y, box_width, box_height), 3)
        
        # Server Address
        addr_label = self.assets.fonts['medium'].render("Server Address:", True, color_config.WHITE)
        self.screen.blit(addr_label, (box_x + 30, box_y + 40))
        
        # Draw address input field
        self.server_connect_input.rect.x = box_x + 30
        self.server_connect_input.rect.y = box_y + 70
        self.server_connect_input.draw(self.screen)
        
        # Server Port
        port_label = self.assets.fonts['medium'].render("Port:", True, color_config.WHITE)
        self.screen.blit(port_label, (box_x + 30, box_y + 140))
        
        # Draw port input field
        self.server_port_input.rect.x = box_x + 30
        self.server_port_input.rect.y = box_y + 170
        self.server_port_input.draw(self.screen)
        
        # Draw test result message
        if self.server_test_result and self.server_test_result_timer > 0:
            self.server_test_result_timer -= 1
            success = self.server_test_result.startswith("Connected")
            result_color = color_config.GREEN if success else color_config.RED
            result_text = self.assets.fonts['small'].render(self.server_test_result, True, result_color)
            result_rect = result_text.get_rect(center=(screen_w // 2, box_y + 230))
            self.screen.blit(result_text, result_rect)
        
        # Button dimensions
        button_width = 140
        button_height = 50
        button_y = box_y + 280
        
        # Test Connection button
        test_btn_x = box_x + 30
        self.server_test_button_rect = pygame.Rect(test_btn_x, button_y, button_width, button_height)
        test_selected = (self.server_selected_index == 2)
        test_color = color_config.YELLOW if test_selected else color_config.UI_BORDER
        pygame.draw.rect(self.screen, test_color, self.server_test_button_rect, 2)
        test_text = self.assets.fonts['small'].render("TEST", True, color_config.WHITE)
        test_rect = test_text.get_rect(center=self.server_test_button_rect.center)
        self.screen.blit(test_text, test_rect)
        
        # Connect button
        connect_btn_x = box_x + box_width - button_width - 30
        self.server_connect_button_rect = pygame.Rect(connect_btn_x, button_y, button_width, button_height)
        connect_selected = (self.server_selected_index == 3)
        connect_color = color_config.GREEN if connect_selected else color_config.UI_BORDER
        pygame.draw.rect(self.screen, connect_color, self.server_connect_button_rect, 2)
        connect_text = self.assets.fonts['small'].render("CONNECT", True, color_config.WHITE)
        connect_rect = connect_text.get_rect(center=self.server_connect_button_rect.center)
        self.screen.blit(connect_text, connect_rect)
        
        # Back button
        back_btn_x = box_x + (box_width - button_width) // 2
        self.server_back_button_rect = pygame.Rect(back_btn_x, button_y + 70, button_width, button_height)
        back_selected = (self.server_selected_index == 4)
        back_color = color_config.RED if back_selected else color_config.UI_BORDER
        pygame.draw.rect(self.screen, back_color, self.server_back_button_rect, 2)
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
        if action == "play_online":  # Multiplayer via network - go to server connect screen
            self._init_server_connect_inputs()
            self.server_selected_index = 0
            self.server_test_result = None
            self.state = GameState.SERVER_CONNECT
            return

        if action == "play":
            logger.info("Game started (via menu)")
            self.init_game()
            self.state = GameState.PLAYING
        elif action == "shop":
            logger.info("Shop opened (via menu)")
            # Ensure player exists for shop access
            if not self.player or self.player is None:
                self.player = Player(game_config.SCREEN_WIDTH // 2, game_config.SCREEN_HEIGHT - 100)
            # Always sync coins from profile when opening shop
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
            logger.info("Game quit (via menu)")
            self.running = False
