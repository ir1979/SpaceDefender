"""
Space Defender - Main Entry Point
Created by Ali Mortazavi
"""

import pygame
from core.game import Game
from systems.save_system import SaveSystem, PlayerProfile
from systems.logger import setup_logging

def main():
    # Initialize logging
    logger = setup_logging()
    logger.info("Starting Space Defender...")
    
    # Start game with profile selection in GUI
    game = Game(None)  # Pass None, profile will be selected in GUI
    game.run()

if __name__ == "__main__":
    main()
