import json

from entities.bullet import BulletFactory, Bullet
from config.settings import game_config


def test_bullet_factory_loads_default_configs_when_missing(tmp_path):
    config_file = tmp_path / "missing_weapons.json"
    assert not config_file.exists()

    BulletFactory._weapon_configs = {}
    BulletFactory.load_configs(str(config_file))

    available = BulletFactory.get_available_types()
    assert "default" in available
    assert "laser" in available
    assert "plasma" in available
    assert "missile" in available


def test_bullet_factory_create_sets_speed_damage_and_angle():
    BulletFactory._weapon_configs = {}
    bullet = BulletFactory.create("laser", 10, 20, -12.5, 3, 30)

    assert isinstance(bullet, Bullet)
    assert bullet.weapon_type == "laser"
    assert bullet.damage == 3
    assert bullet.angle == 30
    assert bullet.speed == -12.5
    assert bullet.velocity_y == -12.5
    assert bullet.rect.centerx == 10
    assert bullet.rect.centery == 20


def test_bullet_update_removes_bullet_off_screen():
    BulletFactory._weapon_configs = {}
    bullet = BulletFactory.create("default", 100, 0, -20, 1, 0)
    bullet.rect.y = -100

    bullet.update()
    assert not bullet.alive()
