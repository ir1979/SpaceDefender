"""
Space Defender - Main Entry Point
Created by Ali Mortazavi
"""

import os
import sys
import argparse
import pygame
from core.game import Game
from systems.save_system import SaveSystem, PlayerProfile
from systems.logger import setup_logging

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Space Defender - Game Entry Point')
    parser.add_argument('mode', nargs='?', default=None, 
                        choices=['game', 'server', 'client'],
                        help='Game mode: game (local), server (listen for clients), client (connect to server)')
    parser.add_argument('--host', default='127.0.0.1', help='Server host (for client mode)')
    parser.add_argument('--port', type=int, default=35555, help='Server port')
    
    args = parser.parse_args()
    
    # Auto-detect client mode if --host or --port are provided
    if args.mode is None:
        # Check if custom host or port were specified (different from defaults)
        host_specified = '--host' in sys.argv
        port_specified = '--port' in sys.argv
        
        if host_specified or port_specified:
            args.mode = 'client'
        else:
            args.mode = 'game'
    
    # Initialize logging
    logger = setup_logging()
    logger.info(f"Starting Space Defender in {args.mode} mode...")
    
    if args.mode == 'server':
        # Run as dedicated server
        from server import main as server_main
        server_main([None, str(args.port)])
    
    elif args.mode == 'client':
        # Run as network client - show menus first, then connect on user action
        game = Game(None, is_server=False)
        # Store server connection details for the menu
        game.server_host = args.host
        game.server_port = args.port
        game.run()
    
    else:
        # Run as local single-player game
        game = Game(None, is_server=False)
        game.run()

if __name__ == "__main__":
    main()
