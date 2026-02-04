"""
Game Configuration Module
Centralized configuration for all game settings
"""
from dataclasses import dataclass
from typing import Tuple
from enum import Enum

@dataclass
class GameConfig:
    """Main game configuration"""
    SCREEN_WIDTH: int = 1024
    SCREEN_HEIGHT: int = 768
    FPS: int = 60
    TITLE: str = "Space Defender"
    VERSION: str = "2.0"
    AUTHOR: str = "Ali Mortazavi"
    
    # Gameplay
    LEVEL_TIME_LIMIT: int = 120
    STARTING_COINS: int = 0
    LEVEL_COIN_BONUS: int = 100
    
    # Paths
    SAVE_FILE: str = "data/profiles.json"
    PLUGIN_DIR: str = "plugins"
    DATA_DIR: str = "data"

@dataclass
class ColorConfig:
    """Color palette"""
    BLACK: Tuple[int, int, int] = (0, 0, 0)
    WHITE: Tuple[int, int, int] = (255, 255, 255)
    RED: Tuple[int, int, int] = (255, 50, 50)
    GREEN: Tuple[int, int, int] = (50, 255, 50)
    BLUE: Tuple[int, int, int] = (50, 150, 255)
    YELLOW: Tuple[int, int, int] = (255, 255, 50)
    PURPLE: Tuple[int, int, int] = (200, 50, 255)
    ORANGE: Tuple[int, int, int] = (255, 150, 50)
    CYAN: Tuple[int, int, int] = (50, 255, 255)
    
    # UI Colors
    UI_BG: Tuple[int, int, int] = (20, 20, 40)
    UI_BORDER: Tuple[int, int, int] = (100, 100, 150)
    UI_TEXT: Tuple[int, int, int] = (220, 220, 255)

@dataclass
class PlayerConfig:
    """Player configuration"""
    SPEED: int = 6
    HEALTH: int = 100
    DAMAGE: int = 25
    FIRE_RATE: int = 10

class GameState(Enum):
    """Game state enumeration"""
    SPLASH_SCREEN = 0
    NAME_INPUT = 1
    PROFILE_SELECT = 2
    MAIN_MENU = 3
    PLAYING = 4
    PAUSED = 5
    SHOP = 6
    GAME_OVER = 7
    LEVEL_COMPLETE = 8
    HIGH_SCORES = 9

# Global instances
game_config = GameConfig()
color_config = ColorConfig()
player_config = PlayerConfig()
