"""
Space Defender - Pure Logic Authoritative Server
"""
import os
import socket
import threading
import time
import sys
from typing import Dict
import traceback

from core.game import Game
from systems.network import send_data, receive_data
from entities.player import Player
from config.settings import game_config, GameState
from systems.logger import get_logger

logger = get_logger('space_defender.server')

# Server configuration
HOST = '127.0.0.1'
DEFAULT_PORT = 35555

clients: Dict[int, socket.socket] = {}
client_inputs: Dict[int, Dict] = {0: {'keys': [], 'shoot': False}, 1: {'keys': [], 'shoot': False}}
shutdown_event = threading.Event()

def get_game_state(game: Game) -> dict:
    """Serializes the game state for clients."""
    if not game.players:
        return {
            'players': [], 
            'enemies': [], 
            'bullets': [], 
            'powerups': [], 
            'score': 0, 
            'level': game.current_level,
            'time_remaining': 0
        }

    return {
        'players': [
            {
                'x': p.rect.centerx,
                'y': p.rect.centery,
                'health': p.health,
                'max_health': p.max_health,
                'coins': getattr(p, 'coins', 0),
                'score': getattr(p, 'score', 0)
            } for p in game.players
        ],
        'enemies': [
            {'x': e.rect.centerx, 'y': e.rect.centery, 'enemy_type': getattr(e, 'enemy_type', 'basic')}
            for e in game.enemies
        ],
        'bullets': [b.get_data() for b in game.bullets],
        'powerups': [p.get_data() for p in game.powerups],
        'score': game.players[0].score if game.players else 0,
        'coins': game.players[0].coins if game.players else 0,
        'level': game.current_level,
        'time_remaining': game.level.time_remaining if game.level else 0,
    }

def client_handler(client_socket: socket.socket, player_id: int):
    """Handles incoming input from a specific player."""
    try:
        while not shutdown_event.is_set():
            data = receive_data(client_socket)
            if data is None: 
                break
            client_inputs[player_id] = data
    except Exception as e:
        logger.error(f"Error in client handler for player {player_id}: {e}")
    finally:
        try:
            client_socket.close()
        except:
            pass
        if player_id in clients: 
            del clients[player_id]
        logger.info(f"Player {player_id} disconnected")
        print(f"[SERVER] Player {player_id + 1} disconnected")

def game_loop():
    """Main simulation loop (Tick rate controlled)."""
    print("[SERVER] Logic thread started.")
    try:
        # Initialize Game with is_server=True
        game = Game(None, is_server=True)
        logger.info(f"Game instance created (server mode)")
        
        # The server runs the simulation
        game.is_network_mode = False

        # Create players with headless=True for server
        game.players.append(Player(game_config.SCREEN_WIDTH // 3, 
                                   game_config.SCREEN_HEIGHT - 100, 
                                   headless=True))
        game.players.append(Player(2 * game_config.SCREEN_WIDTH // 3, 
                                   game_config.SCREEN_HEIGHT - 100, 
                                   headless=True))
        logger.info(f"[SERVER] Created {len(game.players)} player slots (headless mode)")
        print(f"[SERVER] Created {len(game.players)} player slots (headless mode)")

        game.init_game() 
        game.state = GameState.PLAYING 
        logger.info("[SERVER] Game initialized and ready")
        print("[SERVER] Game initialized and ready")
        print("[SERVER] Players can now connect and play")

        target_dt = 1.0 / game_config.FPS
        loop_count = 0
        last_bullet_count = 0
        
        while not shutdown_event.is_set():
            try:
                start_time = time.perf_counter()

                # Process player inputs
                for p_id, inputs in client_inputs.items():
                    if p_id < len(game.players):
                        p = game.players[p_id]
                        k = inputs.get('keys', [])
                        
                        # Apply movement directly
                        dx, dy = 0, 0
                        if 'a' in k: 
                            dx -= p.speed
                        if 'd' in k: 
                            dx += p.speed
                        if 'w' in k: 
                            dy -= p.speed
                        if 's' in k: 
                            dy += p.speed
                        
                        # Update position
                        p.rect.x += dx
                        p.rect.y += dy
                        
                        # Clamp to screen bounds
                        import pygame
                        p.rect.clamp_ip(pygame.Rect(
                            0, 0, game_config.SCREEN_WIDTH, game_config.SCREEN_HEIGHT))
                        
                        # Handle shooting with debug output
                        if inputs.get('shoot'):
                            bullets = p.shoot()
                            if bullets:
                                for b in bullets:
                                    game.bullets.add(b)
                                    game.all_sprites.add(b)
                                print(f"[SERVER] Player {p_id + 1} fired {len(bullets)} bullet(s) at ({p.rect.centerx}, {p.rect.top})")
                                logger.debug(f"Player {p_id} shot {len(bullets)} bullets, cooldown reset to {p.fire_cooldown}")

                # Update game state
                game.update()
                
                # DEBUG: Log bullet count changes
                current_bullet_count = len(game.bullets)
                if current_bullet_count != last_bullet_count:
                    if current_bullet_count > last_bullet_count:
                        print(f"[SERVER] Bullets increased: {last_bullet_count} → {current_bullet_count}")
                    else:
                        print(f"[SERVER] Bullets decreased: {last_bullet_count} → {current_bullet_count} (off-screen or collision)")
                    last_bullet_count = current_bullet_count
                
                # Broadcast state to all connected clients
                state = get_game_state(game)
                for sock in list(clients.values()):
                    try:
                        send_data(sock, state)
                    except Exception as e:
                        logger.warning(f"Failed to send state to client: {e}")

                # Precise sleep for low CPU usage
                elapsed = time.perf_counter() - start_time
                sleep_time = max(0, target_dt - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                loop_count += 1
                if loop_count % 600 == 0:  # Log every 10 seconds at 60 FPS
                    logger.info(f"Game loop: {loop_count} ticks, {len(clients)} clients, {len(game.bullets)} bullets, {len(game.enemies)} enemies")
                    
            except Exception as e:
                logger.error(f"Error in game loop: {e}")
                traceback.print_exc()
                time.sleep(0.05)
    
    except Exception as e:
        logger.critical(f"Fatal error in game_loop: {e}")
        traceback.print_exc()
        shutdown_event.set()

        
def main(argv=None):
    if argv is None:
        argv = sys.argv

    # Get port from terminal argument
    port = int(argv[1]) if len(argv) > 1 else DEFAULT_PORT
    
    print(f"\n{'='*60}")
    print(f"  SPACE DEFENDER - MULTIPLAYER SERVER")
    print(f"{'='*60}")
    print(f"  Host: {HOST}")
    print(f"  Port: {port}")
    print(f"  Max Players: 2")
    print(f"  Mode: Co-op")
    print(f"{'='*60}\n")
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, port))
        server_socket.listen(2)
        logger.info(f"[SERVER] Listening on {HOST}:{port} (GUI Disabled)")
        print(f"[SERVER] Listening on {HOST}:{port}")
        print(f"[SERVER] Waiting for clients to connect...")
        print(f"[SERVER] Press Ctrl+C to stop server\n")
    except Exception as e:
        logger.critical(f"[CRITICAL] Bind failed: {e}")
        print(f"[CRITICAL] Failed to start server: {e}")
        print(f"[CRITICAL] Make sure port {port} is not already in use")
        return

    game_thread = threading.Thread(target=game_loop, daemon=True)
    game_thread.start()
    logger.info("[SERVER] Game loop thread started")

    try:
        while not shutdown_event.is_set():
            server_socket.settimeout(1.0)
            try:
                conn, addr = server_socket.accept()
                p_id = len(clients)
                if p_id < 2:
                    clients[p_id] = conn
                    handler_thread = threading.Thread(target=client_handler, args=(conn, p_id), daemon=True)
                    handler_thread.start()
                    logger.info(f"[SERVER] Player {p_id + 1} connected from {addr}")
                    print(f"[SERVER] ✓ Player {p_id + 1} connected from {addr}")
                    print(f"[SERVER] {len(clients)}/2 players connected")
                else:
                    conn.close()
                    logger.warning(f"[SERVER] Connection rejected from {addr} - server full")
                    print(f"[SERVER] ✗ Connection rejected from {addr} - server full (2/2 players)")
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"Error accepting connection: {e}")
                continue
    except KeyboardInterrupt:
        logger.info("\n[SERVER] Shutting down on user interrupt...")
        print("\n[SERVER] Shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        traceback.print_exc()
    finally:
        shutdown_event.set()
        server_socket.close()
        logger.info("[SERVER] Server shutdown complete")
        print("[SERVER] Server shutdown complete")

if __name__ == "__main__":
    main()
