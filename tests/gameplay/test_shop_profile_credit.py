import pygame

from entities.player import Player
from systems.asset_manager import AssetManager
from systems.save_system import PlayerProfile
from ui.menus import Shop


def test_shop_uses_profile_credit_when_player_funds_are_low():
    pygame.init()
    assets = AssetManager()
    shop = Shop(assets)

    player = Player(100, 100)
    profile = PlayerProfile("shop_credit_test")
    profile.current_coins = 300
    profile.total_coins = 300
    player.current_profile = profile
    player.profile = profile
    player.coins = 50

    shop_credit = shop._get_shop_credit(player)
    assert shop_credit == 300

    atomic_index = next(
        i for i, item in enumerate(shop.items) if item["effect"] == "atomic_bomb"
    )
    shop.purchase(atomic_index, player)

    assert player.get_weapon_count("atomic_bomb") == 1
    assert profile.get_weapon_count("atomic_bomb") == 1
    assert player.coins == 50
    assert profile.coins == 50
    assert profile.total_coins == 50
