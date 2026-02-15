#!/usr/bin/env python3
"""
Shop Testing Script
Tests shop functionality with detailed logging
"""

import sys
import time
import pygame

# Initialize logging FIRST before importing anything else
from systems.logger import setup_logging
logger_instance = setup_logging()

# Now import everything else
from systems.logger import get_logger
from systems.save_system import PlayerProfile, SaveSystem
from entities.player import Player

logger = get_logger('space_defender.shop_test')

def test_shop():
    """Test shop functionality"""
    logger.info("Starting shop test...")
    
    # Initialize pygame
    pygame.init()
    pygame.display.set_mode((100, 100))  # Minimal display for headless testing
    logger.info("Pygame initialized")
    
    # Create a test player
    player = Player(100, 100)
    logger.info(f"Created test player: health={player.health}, coins={player.coins}, damage={player.damage}")
    
    # Give the player some coins
    player.coins = 500
    logger.info(f"Given coins to player: {player.coins}")
    logger.info(f"Player coins after setting: {player.coins}")  # Double check
    
    # Import shop
    from ui.menus import Shop
    from systems.asset_manager import AssetManager
    
    # Create asset manager
    assets = AssetManager()
    logger.info("Created AssetManager")
    
    # Create shop
    shop = Shop(assets)
    logger.info(f"Created Shop with {len(shop.items)} items")
    
    # Log initial shop items
    for i, item in enumerate(shop.items):
        logger.info(f"  [{i}] {item['name']}: cost={item['cost']}, level={item['level']}/{item['max_level']}, effect={item['effect']}")
    
    logger.info(f"ABOUT TO TEST - Player coins: {player.coins}, Item 0 cost: {shop.items[0]['cost']}")
    
    logger.info("="*80)
    logger.info("TEST 1: Purchase Max Health upgrade")
    logger.info("="*80)
    shop.purchase(0, player)
    
    logger.info("="*80)
    logger.info("TEST 2: Purchase Damage upgrade")
    logger.info("="*80)
    shop.purchase(1, player)
    
    logger.info("="*80)
    logger.info("TEST 3: Check player status after purchases")
    logger.info("="*80)
    logger.info(f"Player status: coins={player.coins}, health={player.health}, max_health={player.max_health}, damage={player.damage}")
    
    logger.info("="*80)
    logger.info("TEST 4: Try to purchase with insufficient coins")
    logger.info("="*80)
    player.coins = 10
    logger.info(f"Set player coins to: {player.coins}")
    shop.purchase(0, player)
    
    logger.info("="*80)
    logger.info("Shop test completed!")
    logger.info("="*80)

if __name__ == '__main__':
    test_shop()


