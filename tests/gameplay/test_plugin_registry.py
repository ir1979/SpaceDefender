import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

from plugins.runtime import bootstrap_plugins, reset_plugin_runtime
from plugins.registry import get_enemy_plugin, get_shop_item_plugin, get_weapon_plugin
from entities.bullet import BulletFactory
from entities.enemy import EnemyFactory
from entities.player import Player
from ui.menus import Shop


class DummyAssets:
    def play_sound(self, *_args, **_kwargs):
        pass


def test_plugins_are_discovered_and_registered():
    reset_plugin_runtime()
    EnemyFactory._enemy_configs = {}
    BulletFactory._weapon_configs = {}
    EnemyFactory._create_default_configs()
    BulletFactory._create_default_configs()
    bootstrap_plugins()

    assert get_enemy_plugin("zigzag_bomber") is not None
    assert get_weapon_plugin("homing_missile") is not None
    assert get_shop_item_plugin("shield_booster") is not None


def test_homing_missile_weapon_fires_projectile():
    pygame.init()
    reset_plugin_runtime()
    EnemyFactory._enemy_configs = {}
    BulletFactory._weapon_configs = {}
    EnemyFactory._create_default_configs()
    BulletFactory._create_default_configs()
    bootstrap_plugins()

    player = Player(200, 300, headless=True)
    player.enemy_group = pygame.sprite.Group()
    bullets = player.shoot("homing_missile")
    assert len(bullets) == 1
    assert getattr(bullets[0], "weapon_type", "") == "homing_missile"


def test_plugin_shop_item_purchase_applies_effect():
    pygame.init()
    reset_plugin_runtime()
    EnemyFactory._enemy_configs = {}
    BulletFactory._weapon_configs = {}
    EnemyFactory._create_default_configs()
    BulletFactory._create_default_configs()
    bootstrap_plugins()

    shop = Shop(DummyAssets())
    player = Player(100, 100, headless=True)
    player.coins = 500
    shield_idx = next(i for i, item in enumerate(shop.items) if item["effect"] == "shield_booster")
    shop.purchase(shield_idx, player)

    assert player.has_shield
    assert player.shield_timer >= 480
