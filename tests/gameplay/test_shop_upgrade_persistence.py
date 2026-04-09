import os

import pygame
from systems.asset_manager import AssetManager
from systems.save_system import PlayerProfile, SaveSystem
from entities.player import Player
from ui.menus import Shop
from config.settings import player_config


def test_shop_upgrades_are_saved_and_loaded_from_profile(tmp_path):
    pygame.init()

    profile_name = "upgrade_persist_test"
    profile = PlayerProfile(profile_name)
    profile.total_coins = 500
    profile.current_coins = 500
    SaveSystem.SAVE_FILE = str(tmp_path / "profiles.json")
    SaveSystem.save_profile(profile)

    player = Player(100, 100)
    player.current_profile = profile
    player.profile = profile
    player.coins = 500

    # Use a minimal asset object for the shop
    class DummyAssets:
        def play_sound(self, *_args, **_kwargs):
            pass

    shop = Shop(DummyAssets())
    max_health_index = next(i for i, item in enumerate(shop.items) if item["effect"] == "max_health")
    damage_index = next(i for i, item in enumerate(shop.items) if item["effect"] == "damage")

    shop.purchase(max_health_index, player)
    shop.purchase(damage_index, player)

    profile.sync_after_shop(player.coins)
    SaveSystem.save_profile(profile)

    reloaded = SaveSystem.load_profile(profile_name)
    assert reloaded is not None
    assert reloaded.upgrade_levels["max_health"] == 1
    assert reloaded.upgrade_levels["damage"] == 1
    assert reloaded.total_coins == player.coins

    player2 = Player(200, 200)
    reloaded.apply_upgrades(player2)
    assert player2.max_health == player_config.HEALTH + 20
    assert player2.damage == player_config.DAMAGE + 10
    assert player2.fire_rate == player_config.FIRE_RATE
    assert player2.speed == player_config.SPEED
