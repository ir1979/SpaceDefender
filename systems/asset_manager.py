"""
Asset Manager Module
"""
import pygame
import os
from pathlib import Path

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
        try:
            self.fonts['title'] = pygame.font.Font(None, 72)
            self.fonts['large'] = pygame.font.Font(None, 48)
            self.fonts['medium'] = pygame.font.Font(None, 36)
            self.fonts['small'] = pygame.font.Font(None, 24)
            self.fonts['tiny'] = pygame.font.Font(None, 18)
        except:
            self.fonts['title'] = pygame.font.SysFont('arial', 72, bold=True)
            self.fonts['large'] = pygame.font.SysFont('arial', 48, bold=True)
            self.fonts['medium'] = pygame.font.SysFont('arial', 36)
            self.fonts['small'] = pygame.font.SysFont('arial', 24)
            self.fonts['tiny'] = pygame.font.SysFont('arial', 18)
    
    def load_sounds(self):
        """Load sound effects from data/sounds directory"""
        # Get the space_defender directory (parent of systems folder)
        space_defender_dir = Path(__file__).parent.parent
        sound_dir = space_defender_dir / 'data' / 'sounds'
        
        # Create sounds directory if it doesn't exist
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
                        self.sprites[sprite_name] = pygame.image.load(str(file))
                        loaded_count += 1
                        print(f"  ✓ Loaded sprite: {file.name}")
                    except pygame.error as e:
                        print(f"  ✗ Failed to load {file.name}: {e}")
        
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

    def load_splash_image(self):
        """Load splash screen background image or generate a default one"""
        from config.settings import game_config
        
        space_defender_dir = Path(__file__).parent.parent
        assets_dir = space_defender_dir / 'assets'
        
        # Try to load splash.png if it exists
        splash_path = assets_dir / 'splash.png'
        
        if splash_path.exists():
            try:
                self.splash_image = pygame.image.load(str(splash_path))
                print(f"✓ Loaded splash screen image from {splash_path}")
                return
            except Exception as e:
                print(f"✗ Failed to load splash.png: {e}")
        
        # Generate default splash screen image if not found
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
