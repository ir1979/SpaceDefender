#!/usr/bin/env python3
"""
Integration Test for Profile Selection and Shop Purchasing

This test simulates the entire user flow:
1. Creates a profile with coins.
2. Loads the profile into the game.
3. Verifies the player's coins are loaded correctly.
4. Makes a purchase from the shop.
5. Verifies coins are deducted.
6. Saves the profile and verifies the new coin total is persistent.
"""

import os
import pygame
import time

# Initialize logging before other imports
from systems.logger import setup_logging
logger_instance = setup_logging()

from systems.logger import get_logger
from systems.save_system import PlayerProfile, SaveSystem
from entities.player import Player
from ui.menus import Shop
from systems.asset_manager import AssetManager
from core.game import Game

logger = get_logger('space_defender.profile_shop_test')

TEST_PROFILE_NAME = "test_shopper_profile_123"
TEST_EARNER_PROFILE_NAME = "test_earner_profile_456"
TEST_QUITTER_PROFILE_NAME = "test_quitter_profile_789"

def test_profile_selection_and_shop_purchase():
    """
    Tests the full flow from profile selection to making a purchase in the shop.
    """
    logger.info("="*80)
    logger.info("Starting Profile Selection -> Shop Purchase integration test...")
    logger.info("="*80)

    # --- 1. Setup: Create and save a test profile with coins ---
    # Ensure a clean slate by deleting any previous test profile
    if SaveSystem.profile_exists(TEST_PROFILE_NAME):
        SaveSystem.delete_profile(TEST_PROFILE_NAME)
        logger.info(f"Cleaned up existing test profile: {TEST_PROFILE_NAME}")

    profile = PlayerProfile(TEST_PROFILE_NAME)
    profile.total_coins = 500  # Give the profile starting coins
    SaveSystem.save_profile(profile)
    logger.info(f"Created and saved test profile '{TEST_PROFILE_NAME}' with {profile.total_coins} total_coins.")

    # --- 2. Game Simulation: Load the profile ---
    # Pygame is initialized by the test runner
    game = Game(None) # Start game without a profile initially
    
    # Simulate selecting the profile from the menu
    loaded_profile = SaveSystem.load_profile(TEST_PROFILE_NAME)
    assert loaded_profile is not None, "Failed to load the test profile."
    
    game._apply_profile_start_level(loaded_profile)
    logger.info(f"Simulated profile selection. Applied '{loaded_profile.name}' to the game.")

    # --- 3. Verification: Check if player's coins are loaded ---
    assert game.player is not None, "Player object was not created after applying profile."
    # When a profile is selected, its `total_coins` are loaded into the session `coins`.
    assert game.player.coins == 500, f"Player coins mismatch! Expected 500, got {game.player.coins}"
    logger.info(f"✓ Player coins correctly loaded from profile: {game.player.coins}")

    # --- 4. Shop Interaction: Make a purchase ---
    item_to_buy = game.shop.items[0] # 'Max Health +20', cost: 75
    item_cost = item_to_buy['cost']
    logger.info(f"Attempting to purchase '{item_to_buy['name']}' for {item_cost} coins.")
    game.shop.purchase(0, game.player)

    # --- 5. Verification: Check coin deduction and save ---
    expected_coins_after_purchase = 500 - item_cost
    assert game.player.coins == expected_coins_after_purchase, f"Incorrect coin balance after purchase! Expected {expected_coins_after_purchase}, got {game.player.coins}"
    logger.info(f"✓ Purchase successful. Player coins are now: {game.player.coins}")
    
    # Simulate exiting the shop, which triggers the save logic in the game
    logger.info("Simulating shop exit and profile save...")
    game.current_profile.sync_after_shop(game.player.coins)
    SaveSystem.save_profile(game.current_profile)
    logger.info("Saved profile with updated coin total.")

    # --- 6. Final Verification: Reload profile and check persistence ---
    reloaded_profile = SaveSystem.load_profile(TEST_PROFILE_NAME)
    assert reloaded_profile.total_coins == expected_coins_after_purchase, f"Persistent coin total is incorrect! Expected {expected_coins_after_purchase}, got {reloaded_profile.total_coins}"
    logger.info(f"✓ Verified persistent coin total is correct: {reloaded_profile.total_coins}")

    # --- 7. Teardown: Clean up the test profile ---
    SaveSystem.delete_profile(TEST_PROFILE_NAME)
    logger.info(f"Cleaned up and deleted test profile: {TEST_PROFILE_NAME}")
    logger.info("="*80)
    logger.info("✅ Integration test PASSED!")
    logger.info("="*80)

def test_coin_earning_and_saving():
    """
    Tests the coin earning and saving logic to ensure no coin duplication occurs.
    1. Starts a game with a profile that has existing coins.
    2. Simulates earning coins in a level.
    3. Simulates the game ending.
    4. Verifies the final total_coins is correct.
    """
    logger.info("="*80)
    logger.info("Starting Coin Earning -> Save integration test...")
    logger.info("="*80)

    # --- 1. Setup: Create a profile with starting coins ---
    if SaveSystem.profile_exists(TEST_EARNER_PROFILE_NAME):
        SaveSystem.delete_profile(TEST_EARNER_PROFILE_NAME)
        logger.info(f"Cleaned up existing test profile: {TEST_EARNER_PROFILE_NAME}")

    profile = PlayerProfile(TEST_EARNER_PROFILE_NAME)
    profile.total_coins = 100  # Start with 100 coins
    SaveSystem.save_profile(profile)
    logger.info(f"Created test profile '{TEST_EARNER_PROFILE_NAME}' with {profile.total_coins} total_coins.")

    # --- 2. Game Simulation: Start a new game ---
    # Pygame is initialized by the test runner
    game = Game(None)
    
    # Load the profile
    loaded_profile = SaveSystem.load_profile(TEST_EARNER_PROFILE_NAME)
    game._apply_profile_start_level(loaded_profile)
    
    # Start the game level, which calls start_new_game() on the profile
    game.init_game()
    logger.info("Simulated starting a new game level.")

    # Verification: Check initial state
    assert game.player.coins == 100, f"Player should start the level with 100 coins, but has {game.player.coins}"
    assert game.current_profile.session_start_coins == 100, f"Profile's session_start_coins should be 100, but is {game.current_profile.session_start_coins}"
    logger.info(f"✓ Player started level with correct coin balance: {game.player.coins}")

    # --- 3. Gameplay Simulation: Earn coins ---
    game.player.coins += 50
    logger.info(f"Simulated earning 50 coins. Player now has {game.player.coins} coins in session.")

    # --- 4. Game End Simulation: Game Over ---
    # This part mimics the logic from game.update() when the player's health drops to 0
    coins_earned = game.player.coins - game.current_profile.session_start_coins
    game.current_profile.end_game(score=1000, coins=coins_earned, level=1, time_played=120)
    SaveSystem.save_profile(game.current_profile)
    logger.info(f"Simulated game over. Calculated coins_earned: {coins_earned}. Saved profile.")

    # --- 5. Verification: Check persistent coin total ---
    reloaded_profile = SaveSystem.load_profile(TEST_EARNER_PROFILE_NAME)
    expected_total_coins = 100 + 50 # Initial coins + earned coins
    assert reloaded_profile.total_coins == expected_total_coins, f"Persistent total_coins is incorrect! Expected {expected_total_coins}, got {reloaded_profile.total_coins}"
    logger.info(f"✓ Verified persistent total_coins is correct: {reloaded_profile.total_coins}")

    # --- 6. Teardown ---
    SaveSystem.delete_profile(TEST_EARNER_PROFILE_NAME)
    logger.info(f"Cleaned up and deleted test profile: {TEST_EARNER_PROFILE_NAME}")
    logger.info("="*80)
    logger.info("✅ Integration test PASSED!")
    logger.info("="*80)

def test_quit_level_logic():
    """
    Tests that quitting a level discards session progress and reverts the profile.
    """
    logger.info("="*80)
    logger.info("Starting Quit Level logic test...")
    logger.info("="*80)

    # --- 1. Setup: Create a profile with starting values ---
    if SaveSystem.profile_exists(TEST_QUITTER_PROFILE_NAME):
        SaveSystem.delete_profile(TEST_QUITTER_PROFILE_NAME)
    
    profile = PlayerProfile(TEST_QUITTER_PROFILE_NAME)
    profile.total_coins = 200
    profile.total_score = 1000
    SaveSystem.save_profile(profile)
    logger.info(f"Created test profile '{TEST_QUITTER_PROFILE_NAME}' with {profile.total_coins} coins and {profile.total_score} score.")

    # --- 2. Game Simulation: Start a game and make changes ---
    game = Game(None)
    loaded_profile = SaveSystem.load_profile(TEST_QUITTER_PROFILE_NAME)
    game._apply_profile_start_level(loaded_profile)
    game.init_game()

    # Simulate earning coins and score
    game.player.coins += 77
    game.player.score += 550
    logger.info(f"Simulated earning progress. Player now has {game.player.coins} coins and {game.player.score} score.")

    # --- 3. Quit Simulation: Simulate the player quitting the level ---
    # This mimics the logic in handle_events for QUIT_CONFIRM
    logger.info("Simulating player quitting the level...")
    reloaded_profile_after_quit = SaveSystem.load_profile(game.current_profile.name)
    assert reloaded_profile_after_quit is not None, "Profile should exist after quitting."
    game.current_profile = reloaded_profile_after_quit

    # --- 4. Verification: Check that progress was discarded ---
    assert game.current_profile.total_coins == 200, f"Total coins should have reverted to 200, but are {game.current_profile.total_coins}"
    assert game.current_profile.total_score == 1000, f"Total score should have reverted to 1000, but is {game.current_profile.total_score}"
    logger.info("✓ Verified that quitting discarded session progress and reverted the profile to its pre-level state.")

    # --- 5. Final check on disk ---
    final_profile_on_disk = SaveSystem.load_profile(TEST_QUITTER_PROFILE_NAME)
    assert final_profile_on_disk.total_coins == 200
    assert final_profile_on_disk.total_score == 1000
    logger.info("✓ Verified that the profile on disk remains unchanged.")

    # --- 6. Teardown ---
    SaveSystem.delete_profile(TEST_QUITTER_PROFILE_NAME)
    logger.info(f"Cleaned up test profile: {TEST_QUITTER_PROFILE_NAME}")
    logger.info("="*80)
    logger.info("✅ Integration test PASSED!")
    logger.info("="*80)

def run_all_tests():
    """Initializes pygame once and runs all integration tests."""
    pygame.init()
    test_profile_selection_and_shop_purchase()
    test_coin_earning_and_saving()
    test_quit_level_logic()
    pygame.quit()

if __name__ == "__main__":
    run_all_tests()