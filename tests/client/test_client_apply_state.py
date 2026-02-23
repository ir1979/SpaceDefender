import pytest
import sys
import os

# Add project root to path (go up 3 directories from test file)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Skip this test if pygame isn't available in the test environment
pygame = pytest.importorskip('pygame')

from core.game import Game


def test_apply_server_state_populates_groups():
    # Create a headless Game instance (server-mode will set dummy SDL drivers)
    game = Game(None, is_server=True)
    
    state = {
        'players': [
            {'x': 300, 'y': 400, 'health': 80, 'max_health': 100, 'coins': 5, 'score': 123}
        ],
        'enemies': [
            {'x': 100, 'y': 50, 'enemy_type': 'enemy_basic'}
        ],
        'bullets': [
            {'x': 320, 'y': 390, 'weapon_type': 'default', 'damage': 1, 'angle': 0, 'speed': -10}
        ],
        'powerups': [
            {'x': 200, 'y': 150, 'power_type': 'shield'}
        ],
        'score': 123,
        'level': 1
    }

    game.apply_server_state(state)

    assert len(game.players) == 1
    assert len(game.enemies) == 1
    assert len(game.bullets) == 1
    assert len(game.powerups) == 1

    # Verify some basic attributes were applied
    p = next(iter(game.players))
    assert p.health == 80
    b = next(iter(game.bullets))
    assert hasattr(b, 'damage') and b.damage == 1
    pu = next(iter(game.powerups))
    assert getattr(pu, 'power_type', None) == 'shield'