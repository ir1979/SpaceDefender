import pygame

from entities.player import Player
from systems.particle_system import ParticleSystem
from config.settings import color_config


def test_player_use_weapon_atomic_bomb_decrements_inventory():
    player = Player(100, 100, headless=True)
    player.add_weapon("atomic_bomb")
    player.add_weapon("atomic_bomb")

    assert player.get_weapon_count("atomic_bomb") == 2
    assert player.has_weapon("atomic_bomb")

    assert player.use_weapon("atomic_bomb") is True
    assert player.get_weapon_count("atomic_bomb") == 1
    assert player.has_weapon("atomic_bomb")

    assert player.use_weapon("atomic_bomb") is True
    assert player.get_weapon_count("atomic_bomb") == 0
    assert player.has_weapon("atomic_bomb") is False


def test_particle_system_emits_explosion_and_trail_particles():
    ps = ParticleSystem()
    assert len(ps.particles) == 0

    ps.emit_explosion(200, 200, color_config.YELLOW, count=15)
    assert len(ps.particles) == 15

    ps.emit_trail(200, 200, color_config.YELLOW)
    assert len(ps.particles) == 16

    ps.update()
    assert len(ps.particles) <= 16
    assert len(ps.particles) >= 1


def test_particle_system_draw_does_not_error():
    ps = ParticleSystem()
    surface = pygame.Surface((100, 100))
    ps.emit_trail(10, 10, color_config.YELLOW)
    ps.draw(surface)
    assert surface.get_at((10, 10)) is not None
