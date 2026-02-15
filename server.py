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
DEFAULT_PORT = 9999

clients: Dict[int, socket.socket] = {}
client_inputs: Dict[int, Dict] = {0: {'keys': [], 'shoot': False}, 1: {'keys': [], 'shoot': False}}
shutdown_event = threading.Event()

def get_game_state(game: Game) -> dict:
    """Serializes the game state for clients. Includes detailed
    bullet/powerup payloads so the client can faithfully recreate visuals."""
    if not game.players:
        return {'players': [], 'enemies': [], 'bullets': [], 'powerups': [], 'score': 0, 'level': game.current_level}

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
            {'x': e.rect.centerx, 'y': e.rect.centery, 'enemy_type': getattr(e, 'enemy_type', None)}
            for e in game.enemies
        ],
        'bullets': [b.get_data() for b in game.bullets],
        'powerups': [p.get_data() for p in game.powerups],
        'score': game.players[0].score if game.players else 0,
        'coins': game.players[0].coins if game.players else 0,
        'level': game.current_level,
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

def game_loop():
    """Main simulation loop (Tick rate controlled)."""
    print("[SERVER] Logic thread started.")
    try:
        # Initialize Game with is_server=True
        game = Game(None, is_server=True)
        logger.info(f"Game instance created (server mode)")
        
        # The server runs the simulation, but it is not a "network client".
        # is_network_mode=False ensures it runs the local simulation logic.
        game.is_network_mode = False

        # Create players for the server session. This must be done before init_game().
        game.players.append(Player(game_config.SCREEN_WIDTH // 3, game_config.SCREEN_HEIGHT - 100))
        game.players.append(Player(2 * game_config.SCREEN_WIDTH // 3, game_config.SCREEN_HEIGHT - 100))
        logger.info(f"[SERVER] Created {len(game.players)} player slots.")
        print(f"[SERVER] Created {len(game.players)} player slots.")

        game.init_game() 
        game.state = GameState.PLAYING 
        logger.info("[SERVER] Game initialized and ready")
        print("[SERVER] Game initialized and ready")

        target_dt = 1.0 / game_config.FPS
        loop_count = 0
        
        while not shutdown_event.is_set():
            try:
                start_time = time.perf_counter()

                # Update players using received inputs
                for p_id, inputs in client_inputs.items():
                    if p_id < len(game.players):
                        p = game.players[p_id]
                        k = inputs.get('keys', [])
                        if 'a' in k: p.move(-1, 0)
                        if 'd' in k: p.move(1, 0)
                        if 'w' in k: p.move(0, -1)
                        if 's' in k: p.move(0, 1)
                        if inputs.get('shoot'):
                            bullets = p.shoot()
                            for b in bullets:
                                game.bullets.add(b)
                                game.all_sprites.add(b)

                game.update()
                
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
                if loop_count % 300 == 0:  # Log every 5 seconds at 60 FPS
                    logger.debug(f"Game loop running: {loop_count} iterations, {len(clients)} clients")
                    
            except Exception as e:
                logger.error(f"Error in game loop: {e}")
                traceback.print_exc()
                # Continue running despite errors
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
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, port))
        server_socket.listen(2)
        logger.info(f"[SERVER] Listening on {HOST}:{port} (GUI Disabled)")
        print(f"[SERVER] Listening on {HOST}:{port} (GUI Disabled)")
    except Exception as e:
        logger.critical(f"[CRITICAL] Bind failed: {e}")
        print(f"[CRITICAL] Bind failed: {e}")
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
                    print(f"[SERVER] Player {p_id + 1} connected from {addr}")
                else:
                    conn.close()
                    logger.warning(f"[SERVER] Connection rejected - server full")
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"Error accepting connection: {e}")
                continue
    except KeyboardInterrupt:
        logger.info("\n[SERVER] Closing on user interrupt...")
        print("\n[SERVER] Closing...")
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