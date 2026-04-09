import pytest

from entities.player import Player


def test_weapon_inventory_and_selection():
    player = Player(100, 100, headless=True)

    assert player.get_selected_weapon() == ""
    assert not player.has_weapon("atomic_bomb")
    assert player.get_weapon_count("atomic_bomb") == 0

    player.add_weapon("atomic_bomb")
    player.add_weapon("enemy_freeze")

    assert player.get_weapon_count("atomic_bomb") == 1
    assert player.get_weapon_count("enemy_freeze") == 1
    assert player.has_weapon("atomic_bomb")
    assert player.has_weapon("enemy_freeze")
    assert player.get_selected_weapon() == "atomic_bomb"

    # Adding the same weapon again should not duplicate the weapon list,
    # but should increment the inventory count.
    player.add_weapon("atomic_bomb")
    assert player.get_weapon_count("atomic_bomb") == 2
    assert player.weapons.count("atomic_bomb") == 1

    # Weapon selection cycling wraps correctly.
    player.select_weapon(0)
    assert player.get_selected_weapon() == "atomic_bomb"
    player.cycle_weapon_next()
    assert player.get_selected_weapon() == "enemy_freeze"
    player.cycle_weapon_next()
    assert player.get_selected_weapon() == "atomic_bomb"
    player.cycle_weapon_prev()
    assert player.get_selected_weapon() == "enemy_freeze"

    # Invalid selection index does not change the selection.
    current_weapon = player.get_selected_weapon()
    player.select_weapon(99)
    assert player.get_selected_weapon() == current_weapon

    # Use weapons and verify inventory count updates.
    assert player.use_weapon("atomic_bomb") is True
    assert player.get_weapon_count("atomic_bomb") == 1
    assert player.use_weapon("atomic_bomb") is True
    assert player.get_weapon_count("atomic_bomb") == 0
    assert player.has_weapon("atomic_bomb") is False
    assert player.use_weapon("atomic_bomb") is False
    assert player.get_weapon_count("atomic_bomb") == 0

    assert player.use_weapon("enemy_freeze") is True
    assert player.get_weapon_count("enemy_freeze") == 0
    assert player.has_weapon("enemy_freeze") is False


def test_weapon_use_decrements_profile_inventory():
    player = Player(50, 50, headless=True)
    profile = type("P", (), {"weapon_inventory": {"atomic_bomb": 2}})()
    player.current_profile = profile
    player.profile = profile
    player.add_weapon("atomic_bomb")
    player.add_weapon("atomic_bomb")

    assert player.get_weapon_count("atomic_bomb") == 2
    assert profile.weapon_inventory["atomic_bomb"] == 2

    assert player.use_weapon("atomic_bomb") is True
    assert player.get_weapon_count("atomic_bomb") == 1
    assert profile.weapon_inventory["atomic_bomb"] == 1

    assert player.use_weapon("atomic_bomb") is True
    assert player.get_weapon_count("atomic_bomb") == 0
    assert profile.weapon_inventory["atomic_bomb"] == 0
    assert player.has_weapon("atomic_bomb") is False


def test_use_weapon_without_inventory_returns_false():
    player = Player(50, 50, headless=True)
    assert player.use_weapon("atomic_bomb") is False
    assert player.get_weapon_count("atomic_bomb") == 0
