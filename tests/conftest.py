"""
pytest configuration and fixtures for Space Defender tests
"""

import os
import sys
import pytest

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set up headless pygame for all tests
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

try:
    import pygame
    pygame.init()
except ImportError:
    print("WARNING: pygame not available in test environment")
    pass


@pytest.fixture(scope="session")
def game_config_fixture():
    """Provide game config to tests"""
    from config.settings import game_config
    return game_config


@pytest.fixture
def mock_player():
    """Provide a mock player for testing"""
    from entities.player import Player
    from config.settings import game_config
    player = Player(game_config.SCREEN_WIDTH // 2, game_config.SCREEN_HEIGHT - 100)
    return player
