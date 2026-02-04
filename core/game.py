"""
Main Game Module
"""
import pygame
import random
import math
import time
from typing import List, Tuple
from config.settings import GameState, game_config, color_config
from systems import ParticleSystem, SaveSystem, PlayerProfile, AssetManager
from entities import Player, EnemyFactory, BulletFactory, PowerUp
from ui import HUD, Shop, TextInput

class Level:
    """Level manager"""
    
    def __init__(self, level_num: int):
        self.level_num = level_num
        self.enemies_to_spawn = 10 + (level_num * 5)
        self.enemies_spawned = 0
        self.spawn_timer = 0
        self.spawn_delay = max(40, 80 - (level_num * 3))
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
    def __init__(self, profile):
        pygame.init()
        self.screen = pygame.display.set_mode((game_config.SCREEN_WIDTH, game_config.SCREEN_HEIGHT))
        pygame.display.set_caption(game_config.TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.MAIN_MENU
        self.profile = profile
        self.current_profile = profile  # backward compatibility with older code
        self.session_start_time = time.time()
        self.existing_profiles = SaveSystem.get_profiles()

        # Asset manager
        self.assets = AssetManager()
        EnemyFactory.load_configs('data/enemies.json')
        BulletFactory.load_configs('data/weapons.json')

        # Game objects
        self.player = None
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()

        # Systems
        self.particle_system = ParticleSystem()
        self.hud = HUD(self.assets)
        self.shop = Shop(self.assets)

        # Level
        self.current_level = 1
        self.level = None
        
        # UI Button rectangles for mouse detection
        self.play_button = None
        self.shop_button = None
        self.play_button_hovered = False
        self.shop_button_hovered = False

        # Background
        self.stars = self.create_starfield()

        self._init_game()

    def _init_game(self):
        self.player = Player(game_config.SCREEN_WIDTH // 2, game_config.SCREEN_HEIGHT - 100)
        self.player.coins = self.profile.current_coins
        self.all_sprites.add(self.player)
        self.enemies.empty()
        self.bullets.empty()
        self.powerups.empty()
        self.level = Level(self.current_level)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if self.state == GameState.SHOP:
                if self.shop.handle_input(event, self.player):
                    self.state = GameState.MAIN_MENU
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_s and self.state == GameState.PLAYING:
                    self.state = GameState.SHOP
                elif event.key == pygame.K_p and self.state == GameState.MAIN_MENU:
                    self.state = GameState.PLAYING
                elif event.key == pygame.K_m and self.state == GameState.SHOP:
                    self.state = GameState.MAIN_MENU
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Mouse click handling
                if self.state == GameState.MAIN_MENU:
                    if self.play_button and self.play_button.collidepoint(event.pos):
                        self.state = GameState.PLAYING
                    elif self.shop_button and self.shop_button.collidepoint(event.pos):
                        self.state = GameState.SHOP
                elif self.state == GameState.PLAYING:
                    if self.player:
                        bullets = self.player.shoot()
                        for bullet in bullets:
                            self.bullets.add(bullet)
                            self.all_sprites.add(bullet)
                        if bullets:
                            self.assets.play_sound('shoot', 0.5)
            elif event.type == pygame.MOUSEMOTION and self.state == GameState.MAIN_MENU:
                # Update button hover state
                mouse_pos = event.pos
                if self.play_button:
                    self.play_button_hovered = self.play_button.collidepoint(mouse_pos)
                if self.shop_button:
                    self.shop_button_hovered = self.shop_button.collidepoint(mouse_pos)

    def update(self):
        if self.state == GameState.PLAYING:
            self.all_sprites.update()
            self.particle_system.update()
            self._update_starfield()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                bullets = self.player.shoot()
                for bullet in bullets:
                    self.bullets.add(bullet)
                    self.all_sprites.add(bullet)
                if bullets:  # Only play sound if bullets were created
                    self.assets.play_sound('shoot', 0.5)
        elif self.state == GameState.SHOP:
            # Shop logic here (UI handled in draw)
            pass

    def draw(self):
        self.screen.fill(color_config.BLACK)
        self._draw_starfield()
        if self.state == GameState.PLAYING:
            self.all_sprites.draw(self.screen)
            self.particle_system.draw(self.screen)
            time_remaining = self.level.time_remaining if self.level else 0
            self.hud.draw(self.screen, self.player, self.current_level, time_remaining)
        elif self.state == GameState.SHOP:
            self.shop.draw(self.screen, self.player)
        elif self.state == GameState.MAIN_MENU:
            font = self.assets.get_font('large')
            text = font.render("Space Defender", True, color_config.WHITE)
            self.screen.blit(text, (game_config.SCREEN_WIDTH//2 - 200, 100))
            menu_font = self.assets.get_font('medium')
            
            # Draw Play button
            play_color = color_config.CYAN if self.play_button_hovered else color_config.YELLOW
            play_text = menu_font.render("Press P to Play", True, play_color)
            play_rect = play_text.get_rect(center=(game_config.SCREEN_WIDTH//2, 250))
            # Add padding for clickable area
            self.play_button = play_rect.inflate(100, 30)
            pygame.draw.rect(self.screen, play_color, self.play_button, 2)
            self.screen.blit(play_text, play_rect)
            
            # Draw Shop button
            shop_color = color_config.CYAN if self.shop_button_hovered else color_config.CYAN
            shop_text = menu_font.render("Press S for Shop", True, shop_color)
            shop_rect = shop_text.get_rect(center=(game_config.SCREEN_WIDTH//2, 320))
            # Add padding for clickable area
            self.shop_button = shop_rect.inflate(100, 30)
            pygame.draw.rect(self.screen, shop_color, self.shop_button, 2)
            self.screen.blit(shop_text, shop_rect)
        pygame.display.flip()

    def run(self):
        while self.running:
            self.update()
            self.handle_events()
            self.draw()
            self.clock.tick(game_config.FPS)
        pygame.quit()
    
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
        """Initialize game state"""
        self.player = Player(game_config.SCREEN_WIDTH // 2, game_config.SCREEN_HEIGHT - 100)
        
        # Set coins and score from profile
        if self.current_profile:
            self.player.coins = self.current_profile.current_coins
            self.player.score = self.current_profile.current_score
        
        self.all_sprites.empty()
        self.enemies.empty()
        self.bullets.empty()
        self.powerups.empty()
        
        self.all_sprites.add(self.player)
        self.level = Level(self.current_level)
        self.session_start_time = time.time()
    
    def handle_events(self):
        """Handle all game events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.save_and_exit()
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                if self.state == GameState.SPLASH_SCREEN:
                    if self.existing_profiles:
                        self.state = GameState.PROFILE_SELECT
                    else:
                        self.state = GameState.NAME_INPUT
                        self.text_input = TextInput(
                            game_config.SCREEN_WIDTH // 2 - 200, 350, 400, 60,
                            self.assets.fonts['medium'])
                
                elif self.state == GameState.NAME_INPUT:
                    if self.text_input and self.text_input.handle_event(event):
                        if self.text_input.text.strip():
                            self.current_profile = PlayerProfile(self.text_input.text.strip())
                            self.current_profile.start_new_game()
                            SaveSystem.save_profile(self.current_profile)
                            self.state = GameState.MAIN_MENU
                
                elif self.state == GameState.PROFILE_SELECT:
                    if event.key == pygame.K_n:
                        self.text_input = TextInput(
                            game_config.SCREEN_WIDTH // 2 - 200, 350, 400, 60,
                            self.assets.fonts['medium'])
                        self.state = GameState.NAME_INPUT
                    elif event.key == pygame.K_ESCAPE:
                        self.state = GameState.MAIN_MENU
                    else:
                        profiles = SaveSystem.get_profiles()
                        try:
                            index = int(event.unicode) - 1
                            if 0 <= index < len(profiles):
                                self.current_profile = profiles[index]
                                self.current_profile.start_new_game()
                                self.state = GameState.MAIN_MENU
                        except:
                            pass
                
                elif self.state == GameState.MAIN_MENU:
                    if event.key == pygame.K_RETURN:
                        self.init_game()
                        self.state = GameState.PLAYING
                    elif event.key == pygame.K_h:
                        self.state = GameState.HIGH_SCORES
                    elif event.key == pygame.K_p:
                        self.state = GameState.PROFILE_SELECT
                    elif event.key == pygame.K_ESCAPE:
                        self.save_and_exit()
                        self.running = False
                
                elif self.state == GameState.PLAYING:
                    if event.key == pygame.K_p:
                        self.state = GameState.PAUSED
                    elif event.key == pygame.K_s:
                        self.state = GameState.SHOP
                
                elif self.state == GameState.PAUSED:
                    if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                        self.level.start_time = time.time() - (self.level.time_limit - self.level.time_remaining)
                        self.state = GameState.PLAYING
                
                elif self.state == GameState.SHOP:
                    if self.shop.handle_input(event, self.player):
                        if self.current_profile:
                            self.current_profile.current_coins = self.player.coins
                            SaveSystem.save_profile(self.current_profile)
                        self.state = GameState.PLAYING
                
                elif self.state == GameState.LEVEL_COMPLETE:
                    if event.key == pygame.K_RETURN:
                        self.current_level += 1
                        self.player.coins += game_config.LEVEL_COIN_BONUS
                        
                        if self.current_profile:
                            self.current_profile.current_coins = self.player.coins
                            self.current_profile.current_score = self.player.score
                            self.current_profile.current_level = self.current_level
                            SaveSystem.save_profile(self.current_profile)
                        
                        self.init_game()
                        self.state = GameState.PLAYING
                    elif event.key == pygame.K_ESCAPE:
                        self.state = GameState.MAIN_MENU
                
                elif self.state == GameState.GAME_OVER:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                        if self.current_profile:
                            session_time = time.time() - self.session_start_time
                            self.current_profile.end_game(
                                self.player.score, 
                                self.player.coins,
                                self.current_level,
                                session_time
                            )
                            SaveSystem.save_profile(self.current_profile)
                            SaveSystem.save_high_score(
                                self.current_profile,
                                self.player.score,
                                self.current_level
                            )
                        
                        self.current_level = 1
                        if self.current_profile:
                            self.current_profile.start_new_game()
                        self.state = GameState.MAIN_MENU
                
                elif self.state == GameState.HIGH_SCORES:
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.MAIN_MENU

            # Mouse click handling (left-click)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == GameState.MAIN_MENU:
                    # Click play or shop buttons
                    if self.play_button and self.play_button.collidepoint(event.pos):
                        self.init_game()
                        self.state = GameState.PLAYING
                    elif self.shop_button and self.shop_button.collidepoint(event.pos):
                        self.state = GameState.SHOP
                elif self.state == GameState.PLAYING:
                    if self.player:
                        bullets = self.player.shoot()
                        for bullet in bullets:
                            self.bullets.add(bullet)
                            self.all_sprites.add(bullet)
                            self.particle_system.emit_trail(
                                bullet.rect.centerx, bullet.rect.centery, color_config.YELLOW)
                        if bullets:
                            self.assets.play_sound('shoot', 0.5)

            # Mouse motion for hover effects in main menu
            elif event.type == pygame.MOUSEMOTION and self.state == GameState.MAIN_MENU:
                mouse_pos = event.pos
                if self.play_button:
                    self.play_button_hovered = self.play_button.collidepoint(mouse_pos)
                if self.shop_button:
                    self.shop_button_hovered = self.shop_button.collidepoint(mouse_pos)
    
    def save_and_exit(self):
        if self.current_profile and self.player:
            self.current_profile.current_coins = self.player.coins
            self.current_profile.current_score = self.player.score
            self.current_profile.current_level = self.current_level
            SaveSystem.save_profile(self.current_profile)
    
    def update(self):
        """Update game state"""
        if self.state == GameState.SPLASH_SCREEN:
            self.splash_timer += 1
            if self.splash_timer >= self.splash_duration:
                if self.existing_profiles:
                    self.state = GameState.PROFILE_SELECT
                else:
                    self.state = GameState.NAME_INPUT
                    self.text_input = TextInput(
                        game_config.SCREEN_WIDTH // 2 - 200, 350, 400, 60,
                        self.assets.fonts['medium'])
                self.splash_timer = 0
            return
        
        if self.state == GameState.NAME_INPUT and self.text_input:
            self.text_input.update()
        
        if self.state == GameState.PLAYING:
            # Update timer
            if not self.level.update_timer():
                if self.current_profile:
                    session_time = time.time() - self.session_start_time
                    self.current_profile.end_game(
                        self.player.score,
                        self.player.coins,
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
            self.particle_system.update()
            
            # Player shooting
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                new_bullets = self.player.shoot()
                for bullet in new_bullets:
                    self.bullets.add(bullet)
                    self.all_sprites.add(bullet)
                    self.particle_system.emit_trail(
                        bullet.rect.centerx, bullet.rect.centery, color_config.YELLOW)
            
            # Spawn enemies
            if self.level.should_spawn_enemy():
                enemy_type = EnemyFactory.get_random_type(self.current_level)
                enemy = EnemyFactory.create(
                    enemy_type, 
                    random.randint(50, game_config.SCREEN_WIDTH - 50),
                    -50,
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
                    self.assets.play_sound('enemy_hit', 0.7)
                    for enemy in hit_enemies:
                        enemy.health -= bullet.damage
                        if enemy.health <= 0:
                            self.particle_system.emit_explosion(
                                enemy.rect.centerx, enemy.rect.centery,
                                color_config.RED, 30)
                            self.assets.play_sound('explosion', 0.8)
                            self.player.coins += enemy.coin_value
                            self.player.score += enemy.score_value
                            enemy.kill()
                        else:
                            self.particle_system.emit_explosion(
                                bullet.rect.centerx, bullet.rect.centery,
                                color_config.ORANGE, 10)
            
            # Check player-enemy collisions
            hit_enemies = pygame.sprite.spritecollide(self.player, self.enemies, True)
            for enemy in hit_enemies:
                self.player.take_damage(30)
                self.particle_system.emit_explosion(
                    enemy.rect.centerx, enemy.rect.centery, color_config.RED, 25)
                
                if self.player.health <= 0:
                    self.assets.play_sound('game_over', 0.8)
                    if self.current_profile:
                        session_time = time.time() - self.session_start_time
                        self.current_profile.end_game(
                            self.player.score,
                            self.player.coins,
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
            
            # Check player-powerup collisions
            hit_powerups = pygame.sprite.spritecollide(self.player, self.powerups, True)
            for powerup in hit_powerups:
                self.player.activate_powerup(powerup.power_type)
                self.assets.play_sound('powerup', 0.8)
                self.particle_system.emit_explosion(
                    powerup.rect.centerx, powerup.rect.centery, color_config.GREEN, 20)
            
            # Check level complete
            if (self.level.enemies_spawned >= self.level.enemies_to_spawn and
                len(self.enemies) == 0):
                self.assets.play_sound('level_complete', 0.8)
                self.state = GameState.LEVEL_COMPLETE
        
        # Always update starfield
        self.update_starfield()
    def draw(self):
        """Draw everything"""
        self.screen.fill(color_config.BLACK)
        self.draw_starfield()
        
        if self.state == GameState.SPLASH_SCREEN:
            self.draw_splash_screen()
        
        elif self.state == GameState.NAME_INPUT:
            self.draw_name_input()
        
        elif self.state == GameState.PROFILE_SELECT:
            self.draw_profile_select()
        
        elif self.state == GameState.MAIN_MENU:
            self.draw_main_menu()
        
        elif self.state == GameState.PLAYING:
            if self.player and self.level:
                self.all_sprites.draw(self.screen)
                
                for enemy in self.enemies:
                    enemy.draw_health_bar(self.screen)
                
                self.particle_system.draw(self.screen)
                self.hud.draw(self.screen, self.player, self.current_level, 
                             self.level.time_remaining)
        
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
        
        pygame.display.flip()
    
    def draw_splash_screen(self):
        """Draw splash screen"""
        alpha = 255
        if self.splash_timer < self.splash_fade_in:
            alpha = int(255 * (self.splash_timer / self.splash_fade_in))
        elif self.splash_timer > (self.splash_duration - self.splash_fade_out):
            remaining = self.splash_duration - self.splash_timer
            alpha = int(255 * (remaining / self.splash_fade_out))
        
        center_x = game_config.SCREEN_WIDTH // 2
        center_y = game_config.SCREEN_HEIGHT // 2
        
        # Animated circles
        for i in range(3):
            radius = 50 + (i * 30) + int(math.sin(self.splash_timer * 0.05 + i) * 10)
            circle_alpha = max(0, alpha - (i * 50))
            circle_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(circle_surface, (*color_config.CYAN, circle_alpha // 3), 
                             (radius, radius), radius, 3)
            circle_rect = circle_surface.get_rect(center=(center_x, center_y))
            self.screen.blit(circle_surface, circle_rect)
        
        # Title
        title_text = "SPACE DEFENDER"
        title_font = self.assets.fonts['title']
        
        for offset in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
            glow_surface = title_font.render(title_text, True, color_config.CYAN)
            glow_surface.set_alpha(alpha // 4)
            glow_rect = glow_surface.get_rect(
                center=(center_x + offset[0], center_y - 100 + offset[1]))
            self.screen.blit(glow_surface, glow_rect)
        
        title_surface = title_font.render(title_text, True, color_config.WHITE)
        title_surface.set_alpha(alpha)
        title_rect = title_surface.get_rect(center=(center_x, center_y - 100))
        self.screen.blit(title_surface, title_rect)
        
        # Line
        line_width = 400
        line_y = center_y - 20
        pygame.draw.line(self.screen, (*color_config.CYAN, alpha),
                        (center_x - line_width // 2, line_y),
                        (center_x + line_width // 2, line_y), 3)
        
        # Creator
        created_by = "Created by"
        created_surface = self.assets.fonts['medium'].render(created_by, True, color_config.UI_TEXT)
        created_surface.set_alpha(alpha)
        created_rect = created_surface.get_rect(center=(center_x, center_y + 40))
        self.screen.blit(created_surface, created_rect)
        
        # Name
        name_text = "Ali Mortazavi"
        name_font = self.assets.fonts['large']
        
        for offset in [(1, 1), (-1, -1), (1, -1), (-1, 1)]:
            name_glow = name_font.render(name_text, True, color_config.CYAN)
            name_glow.set_alpha(alpha // 3)
            name_glow_rect = name_glow.get_rect(
                center=(center_x + offset[0], center_y + 100 + offset[1]))
            self.screen.blit(name_glow, name_glow_rect)
        
        name_surface = name_font.render(name_text, True, color_config.CYAN)
        name_surface.set_alpha(alpha)
        name_rect = name_surface.get_rect(center=(center_x, center_y + 100))
        self.screen.blit(name_surface, name_rect)
        
        # Year
        year_text = "2026"
        year_surface = self.assets.fonts['small'].render(year_text, True, color_config.UI_TEXT)
        year_surface.set_alpha(alpha)
        year_rect = year_surface.get_rect(center=(center_x, center_y + 150))
        self.screen.blit(year_surface, year_rect)
        
        # Skip hint
        if self.splash_timer > self.splash_fade_in:
            skip_text = "Press any key to continue"
            skip_surface = self.assets.fonts['small'].render(skip_text, True, color_config.WHITE)
            skip_alpha = int(alpha * (0.5 + 0.5 * math.sin(self.splash_timer * 0.1)))
            skip_surface.set_alpha(skip_alpha)
            skip_rect = skip_surface.get_rect(
                center=(center_x, game_config.SCREEN_HEIGHT - 80))
            self.screen.blit(skip_surface, skip_rect)
    
    def draw_name_input(self):
        """Draw name input screen"""
        title = self.assets.fonts['large'].render("Enter Your Name", True, color_config.CYAN)
        title_rect = title.get_rect(center=(game_config.SCREEN_WIDTH // 2, 250))
        self.screen.blit(title, title_rect)
        
        if self.text_input:
            self.text_input.draw(self.screen)
        
        hint = self.assets.fonts['small'].render(
            "Press ENTER when done", True, color_config.UI_TEXT)
        hint_rect = hint.get_rect(center=(game_config.SCREEN_WIDTH // 2, 450))
        self.screen.blit(hint, hint_rect)
    
    def draw_profile_select(self):
        """Draw profile selection screen"""
        title = self.assets.fonts['large'].render("Select Profile", True, color_config.CYAN)
        title_rect = title.get_rect(center=(game_config.SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        profiles = SaveSystem.get_profiles()
        y_offset = 200
        
        for i, profile in enumerate(profiles[:5]):
            box_rect = pygame.Rect(200, y_offset, 624, 80)
            pygame.draw.rect(self.screen, color_config.UI_BG, box_rect)
            pygame.draw.rect(self.screen, color_config.UI_BORDER, box_rect, 2)
            
            num_text = f"{i + 1}."
            num_surface = self.assets.fonts['medium'].render(num_text, True, color_config.YELLOW)
            self.screen.blit(num_surface, (220, y_offset + 10))
            
            name_surface = self.assets.fonts['medium'].render(profile.name, True, color_config.WHITE)
            self.screen.blit(name_surface, (280, y_offset + 10))
            
            stats_text = f"Lvl {profile.highest_level} | Score: {profile.total_score} | Coins: {profile.total_coins}"
            stats_surface = self.assets.fonts['small'].render(stats_text, True, color_config.UI_TEXT)
            self.screen.blit(stats_surface, (280, y_offset + 45))
            
            y_offset += 100
        
        new_profile = self.assets.fonts['medium'].render(
            "N - New Profile", True, color_config.GREEN)
        new_rect = new_profile.get_rect(center=(game_config.SCREEN_WIDTH // 2, y_offset + 50))
        self.screen.blit(new_profile, new_rect)
        
        hint = self.assets.fonts['small'].render(
            "Press number to select profile | ESC to skip",
            True, color_config.UI_TEXT)
        hint_rect = hint.get_rect(center=(game_config.SCREEN_WIDTH // 2, y_offset + 100))
        self.screen.blit(hint, hint_rect)
    
    def draw_main_menu(self):
        """Draw main menu"""
        title = self.assets.fonts['title'].render("SPACE DEFENDER", True, color_config.CYAN)
        title_rect = title.get_rect(center=(game_config.SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)
        
        if self.current_profile:
            welcome = self.assets.fonts['medium'].render(
                f"Welcome, {self.current_profile.name}!", True, color_config.GREEN)
            welcome_rect = welcome.get_rect(center=(game_config.SCREEN_WIDTH // 2, 250))
            self.screen.blit(welcome, welcome_rect)
            
            stats_text = f"Total Score: {self.current_profile.total_score} | " \
                        f"Total Coins: {self.current_profile.total_coins} | " \
                        f"Best Level: {self.current_profile.highest_level}"
            stats = self.assets.fonts['small'].render(stats_text, True, color_config.UI_TEXT)
            stats_rect = stats.get_rect(center=(game_config.SCREEN_WIDTH // 2, 290))
            self.screen.blit(stats, stats_rect)
        
        options = [
            ("PRESS ENTER TO START", 380),
            ("H - HIGH SCORES", 450),
            ("P - CHANGE PROFILE", 520),
            ("ESC - QUIT", 590)
        ]
        
        for text, y in options:
            surface = self.assets.fonts['medium'].render(text, True, color_config.WHITE)
            rect = surface.get_rect(center=(game_config.SCREEN_WIDTH // 2, y))
            self.screen.blit(surface, rect)
    
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
            for i, entry in enumerate(scores[:10]):
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
    
    def run(self):
        """Main game loop"""
        while self.running:
            self.clock.tick(game_config.FPS)
            self.handle_events()
            self.update()
            self.draw()
        
        pygame.quit()
