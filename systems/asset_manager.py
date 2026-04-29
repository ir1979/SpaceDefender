"""
Asset Manager Module
"""
import pygame
import os
import random
from pathlib import Path
from typing import Optional

class AssetManager:
    """Manages all game assets"""
    
    def __init__(self):
        self.fonts = {}
        self.sounds = {}
        self.sprites = {}  # Image-based sprites for entities
        self.splash_image = None  # Splash screen background
        self.sound_enabled = True
        
        # Initialize pygame mixer for sound playback
        try:
            pygame.mixer.init()
            print("Pygame mixer initialized successfully")
        except Exception as e:
            print(f"Failed to initialize mixer: {e}")
            self.sound_enabled = False
        
        self.load_fonts()
        self.load_sounds()
        self.load_sprites()
        self.load_splash_image()
    
    def load_fonts(self):
        from config.settings import game_config
        # Scale fonts relative to a 1024×768 reference resolution so the UI
        # looks correct at any screen size (windowed or fullscreen).
        scale = min(game_config.SCREEN_WIDTH / 1024.0, game_config.SCREEN_HEIGHT / 768.0)
        sizes = {
            'title':  max(32, int(72 * scale)),
            'large':  max(24, int(48 * scale)),
            'medium': max(16, int(36 * scale)),
            'small':  max(12, int(24 * scale)),
            'tiny':   max(10, int(18 * scale)),
        }
        try:
            for name, size in sizes.items():
                self.fonts[name] = pygame.font.Font(None, size)
        except Exception:
            for name, size in sizes.items():
                bold = name in ('title', 'large')
                self.fonts[name] = pygame.font.SysFont('arial', size, bold=bold)
    
    def load_sounds(self):
        """Load sound effects from assets/sounds directory (fallback to data/sounds).
        Files were moved to `assets/sounds` — keep backward compatibility by
        falling back to `data/sounds` if needed."""
        # Get the space_defender directory (parent of systems folder)
        space_defender_dir = Path(__file__).parent.parent
        # Prefer assets/sounds; fall back to data/sounds for older checkouts
        sound_dir = space_defender_dir / 'assets' / 'sounds'
        if not sound_dir.exists():
            sound_dir = space_defender_dir / 'data' / 'sounds'
        
        # Ensure directory exists so subsequent code can safely operate
        sound_dir.mkdir(parents=True, exist_ok=True)
        
        # Sound file mappings
        sound_files = {
            'shoot': 'shoot.wav',
            'enemy_hit': 'enemy_hit.wav',
            'explosion': 'explosion.wav',
            'powerup': 'powerup.wav',
            'coin': 'coin.wav',
            'game_over': 'game_over.wav',
            'level_complete': 'level_complete.wav',
            'shop_purchase': 'shop_purchase.wav',
            'menu_select': 'menu_select.wav',
            'splash': 'splash.wav',
        }
        
        print(f"\nLoading sounds from {sound_dir}/...")
        loaded_count = 0
        
        # Load each sound file
        for sound_name, filename in sound_files.items():
            filepath = sound_dir / filename
            try:
                if filepath.exists():
                    self.sounds[sound_name] = pygame.mixer.Sound(str(filepath))
                    loaded_count += 1
                    print(f"  ✓ Loaded: {filename}")
                else:
                    self.sounds[sound_name] = None
                    print(f"  ✗ Not found: {filepath}")
            except pygame.error as e:
                print(f"  ✗ Failed to load {filename}: {e}")
                self.sounds[sound_name] = None
        
        print(f"Loaded {loaded_count}/{len(sound_files)} sounds\n")
    
    def play_sound(self, sound_name: str, volume: float = 1.0):
        """Play a sound effect (with debug info)"""
        if not self.sound_enabled:
            print("Sound disabled; not playing")
            return
        
        sound = self.sounds.get(sound_name)
        mixer_init = pygame.mixer.get_init()
        num_channels = pygame.mixer.get_num_channels()
        if sound:
            try:
                vol = max(0, min(1, volume))  # Clamp volume 0-1
                sound.set_volume(vol)
                ch = sound.play()
                print(f"Playing sound '{sound_name}' (vol={vol}) -> sound_obj={sound}, channel={ch}, mixer_init={mixer_init}, num_channels={num_channels}")
                if ch is None:
                    print(f"Warning: No channel available to play '{sound_name}'")
            except Exception as e:
                print(f"Error playing sound '{sound_name}': {e}, mixer_init={mixer_init}")
        else:
            print(f"Sound '{sound_name}' not loaded; mixer_init={mixer_init}, num_channels={num_channels}")
    
    def get_font(self, size: str):
        """Get font by size name"""
        return self.fonts.get(size, self.fonts['medium'])
    
    def load_sprites(self):
        """Load sprite images from assets directory"""
        space_defender_dir = Path(__file__).parent.parent
        assets_dir = space_defender_dir / 'assets' / 'sprites'
        
        # Create assets directory if it doesn't exist
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Supported image formats
        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
        
        print(f"\nLoading sprites from {assets_dir}/...")
        loaded_count = 0
        
        # Scan for all image files in assets/sprites directory
        if assets_dir.exists():
            for file in assets_dir.iterdir():
                if file.suffix.lower() in image_extensions:
                    try:
                        sprite_name = file.stem  # Filename without extension
                        sprite = pygame.image.load(str(file))
                        self.sprites[sprite_name] = sprite.convert_alpha()
                        loaded_count += 1
                        print(f"  ✓ Loaded sprite: {file.name}")
                    except pygame.error as e:
                        print(f"  ✗ Failed to load {file.name}: {e}")

        # Load helper drone images from assets/updaits/updit3 and map them to engine1..engineN
        custom_drone_dir = space_defender_dir / 'assets' / 'updaits' / 'updit3'
        if custom_drone_dir.exists():
            custom_files = sorted(
                [f for f in custom_drone_dir.iterdir() if f.suffix.lower() in image_extensions]
            )
            for idx, file in enumerate(custom_files, start=1):
                sprite_name = f'engine{idx}'
                try:
                    sprite = pygame.image.load(str(file))
                    self.sprites[sprite_name] = sprite.convert_alpha()
                    loaded_count += 1
                    print(f"  ✓ Loaded custom drone sprite: {file.name} as {sprite_name}")
                except pygame.error as e:
                    print(f"  ✗ Failed to load custom drone sprite {file.name}: {e}")
        
        if loaded_count == 0:
            print(f"  No sprite files found in {assets_dir}")
            print(f"  Sprites will fall back to procedural shapes")
        else:
            print(f"Loaded {loaded_count} sprite(s)\n")
    
    def get_sprite(self, sprite_name: str):
        """Get sprite image if available, None otherwise"""
        return self.sprites.get(sprite_name)
    
    def has_sprite(self, sprite_name: str) -> bool:
        """Check if a sprite exists"""
        return sprite_name in self.sprites
    
    def toggle_sound(self):
        """Toggle sound on/off"""
        self.sound_enabled = not self.sound_enabled

    def get_level_background(self, level_num: int) -> pygame.Surface:
        """Load a custom background for the requested level or generate one."""
        from config.settings import game_config

        background_dir = Path(__file__).parent.parent / game_config.BACKGROUND_DIR
        background_dir.mkdir(parents=True, exist_ok=True)

        custom_path = self._find_level_background_file(background_dir, level_num)
        if custom_path is not None:
            try:
                background = pygame.image.load(str(custom_path))
                return pygame.transform.scale(
                    background.convert_alpha(),
                    (game_config.SCREEN_WIDTH, game_config.SCREEN_HEIGHT)
                )
            except Exception as e:
                print(f"✗ Failed to load custom background {custom_path}: {e}")

        generated = self._generate_level_background(
            game_config.SCREEN_WIDTH,
            game_config.SCREEN_HEIGHT,
            level_num
        )

        save_path = background_dir / f"level_{level_num}.png"
        try:
            pygame.image.save(generated, str(save_path))
            print(f"✓ Generated and saved background for level {level_num}: {save_path}")
        except Exception as e:
            print(f"✗ Failed to save generated background {save_path}: {e}")

        return generated

    def _find_level_background_file(self, background_dir: Path, level_num: int) -> Optional[Path]:
        candidates = [
            f"level_{level_num}",
            f"level-{level_num}",
            f"background_{level_num}",
            f"background-{level_num}",
        ]
        extensions = ['.png', '.jpg', '.jpeg', '.bmp']
        for base in candidates:
            for ext in extensions:
                candidate = background_dir / f"{base}{ext}"
                if candidate.exists():
                    return candidate
        return None

    def _generate_level_background(self, width: int, height: int, level_num: int) -> pygame.Surface:
        """Generate a procedural level background and return it as a surface."""
        surface = pygame.Surface((width, height))

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

        # Add a large faint planet in the background for space defender vibe
        if random.random() > 0.3:  # 70% chance to have a planet
            planet_surface = pygame.Surface((width, height), pygame.SRCALPHA)
            planet_color = random.choice([
                (40, 80, 120), (120, 40, 40), (80, 120, 60), (100, 60, 120), (160, 140, 40)
            ])
            planet_radius = random.randint(min(width, height) // 3, min(width, height) // 2)
            planet_x = random.choice([0, width])
            planet_y = random.choice([0, height])
            
            # Base planet arc
            pygame.draw.circle(planet_surface, (*planet_color, 60), (planet_x, planet_y), planet_radius)
            pygame.draw.circle(planet_surface, (*planet_color, 90), (planet_x, planet_y), int(planet_radius * 0.95))
            
            # Craters
            for _ in range(random.randint(5, 12)):
                crater_radius = random.randint(10, 40)
                cx = planet_x + random.randint(-planet_radius, planet_radius)
                cy = planet_y + random.randint(-planet_radius, planet_radius)
                if (cx - planet_x)**2 + (cy - planet_y)**2 < (planet_radius - crater_radius)**2:
                    pygame.draw.circle(planet_surface, (10, 10, 20, 40), (cx, cy), crater_radius)
                    
            surface.blit(planet_surface, (0, 0))

        # Add a subtle tactical grid
        grid_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        grid_alpha = 12
        grid_color = (0, 255, 255, grid_alpha)
        grid_size = 50
        for x in range(0, width, grid_size):
            pygame.draw.line(grid_surface, grid_color, (x, 0), (x, height))
        for y in range(0, height, grid_size):
            pygame.draw.line(grid_surface, grid_color, (0, y), (width, y))
        surface.blit(grid_surface, (0, 0), special_flags=pygame.BLEND_ADD)

        return surface

    def load_splash_image(self):
        """Load splash screen background image or generate a default one"""
        from config.settings import game_config
        
        space_defender_dir = Path(__file__).parent.parent
        assets_dir = space_defender_dir / 'assets'
        
        # Load splash images from the assets/splash folder
        splash_dir = assets_dir / 'splash'
        if splash_dir.exists():
            image_files = [
                f for f in sorted(splash_dir.iterdir())
                if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
            ]
            if image_files:
                chosen_path = random.choice(image_files)
                try:
                    splash_image = pygame.image.load(str(chosen_path)).convert_alpha()
                    self.splash_image = pygame.transform.scale(
                        splash_image,
                        (game_config.SCREEN_WIDTH, game_config.SCREEN_HEIGHT),
                    )
                    print(f"✓ Loaded splash screen image from {chosen_path}")
                    return
                except Exception as e:
                    print(f"✗ Failed to load splash image {chosen_path}: {e}")

        # Fallback: generate default splash screen image
        print("Generating default splash screen background...")
        self.splash_image = self._generate_splash_background(
            game_config.SCREEN_WIDTH, 
            game_config.SCREEN_HEIGHT
        )
    
    def _generate_splash_background(self, width: int, height: int) -> pygame.Surface:
        """Generate a procedural space-themed splash screen background"""
        from config.settings import color_config
        import random
        
        surface = pygame.Surface((width, height))
        
        # Dark space background with gradient effect
        for y in range(height):
            ratio = y / height
            r = int(10 + ratio * 40)
            g = int(20 + ratio * 30)
            b = int(50 + ratio * 100)
            pygame.draw.line(surface, (r, g, b), (0, y), (width, y))
        
        # Add some stars for atmosphere
        random.seed(42)  # Reproducible star pattern
        for _ in range(150):
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.randint(1, 3)
            brightness = random.randint(100, 255)
            pygame.draw.circle(surface, (brightness, brightness, brightness), (x, y), size)
        
        return surface
    
    def get_splash_image(self) -> pygame.Surface:
        """Get the splash screen background image"""
        return self.splash_image
