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
    
    def toggle_sound(self):
        """Toggle sound on/off"""
        self.sound_enabled = not self.sound_enabled
