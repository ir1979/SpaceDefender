import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame
import pytest

from entities.player import Player
from entities.enemy import Enemy, EnemyFactory
from ui.menus import Shop


class DummyAssets:
    def play_sound(self, *_args, **_kwargs):
        pass


def test_shop_purchases_new_unique_weapons():
    pygame.init()
    player = Player(100, 100, headless=True)
    player.coins = 2500
    shop = Shop(DummyAssets())

    weapon_effects = [
        'shockwave',
        'chain_lightning',
        'time_warp',
        'spread_burst',
        'meteor_strike',
    ]

    for effect in weapon_effects:
        idx = next(i for i, item in enumerate(shop.items) if item['effect'] == effect)
        shop.purchase(idx, player)
        assert player.has_weapon(effect)
        assert player.get_weapon_count(effect) == 1

    assert player.get_selected_weapon() in weapon_effects


def test_enemy_slow_effect_reduces_movement_and_draws_health_bar():
    pygame.init()
    enemy = EnemyFactory.create('basic', 100, 50)
    assert enemy is not None
    enemy.slow_timer = 3
    enemy.slow_factor = 0.25

    original_y = enemy.rect.y
    enemy.update()
    assert enemy.rect.y > original_y
    assert enemy.slow_timer == 2

    surface = pygame.Surface((200, 200))
    enemy.draw_health_bar(surface)
    assert surface.get_at((enemy.rect.x + 1, enemy.rect.y - 10)) is not None
