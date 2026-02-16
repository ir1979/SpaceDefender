"""
Space Defender - Improved Authoritative Server
Performance Improvements:
- 60 FPS tick rate (up from 30) for more responsive gameplay
- Faster waiting state broadcast (0.2s instead of 0.5s)
- Timeout protection for waiting state (60 seconds max)
- Better client disconnect handling
- Optimized state broadcast
"""
import os
import socket
import threading
import time
import random
import sys
import argparse
from typing import Dict
import traceback

from core.game import Game
from systems.network import send_data, receive_data
from entities.player import Player
from entities.enemy import EnemyFactory
from entities.powerup import PowerUp
from config.settings import game_config, GameState
from systems.logger import get_logger

logger = get_logger('space_defender.server')

# Server configuration
HOST = '127.0.0.1'
DEFAULT_PORT = 35555
VERBOSE_LEVEL = 1  # Default verbosity level (0-3)

# Performance tuning
SERVER_FPS = 60  # Increased from 30 for better responsiveness
WAITING_BROADCAST_INTERVAL = 0.2  # Reduced from 0.5s for faster updates
WAITING_TIMEOUT = 30.0  # Maximum time to wait for players (60 seconds)

def vprint(msg, level=1, end='\n'):
    """Print message based on configured verbosity level.
    
    Levels:
    0 - Silent (errors only)
    1 - Low (connections, key events)
    2 - Medium (above + enemy/bullet details)
    3 - High (all debug info)
    """
    if VERBOSE_LEVEL >= level:
        print(msg, end=end)

clients: Dict[int, socket.socket] = {}
client_inputs: Dict[int, Dict] = {0: {'keys': [], 'shoot': False}, 1: {'keys': [], 'shoot': False}}
shutdown_event = threading.Event()
game_start_event = threading.Event()

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
            'time_remaining': 0,
            'game_state_enum': game.state.value
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
        'game_state_enum': game.state.value
    }

def client_handler(client_socket: socket.socket, player_id: int):
    """Handles incoming input from a specific player."""
    try:
        while not shutdown_event.is_set():
            data = receive_data(client_socket)
            if data is None: 
                break
            # Data can be game inputs or game-state updates (e.g., client gone to GAME_OVER)
            if isinstance(data, dict):
                if data.get('message') == 'game_over':
                    # Client is signaling game over; we can log it
                    logger.info(f"Player {player_id} signaled GAME_OVER")
                    vprint(f"[SERVER] Player {player_id + 1} signaled GAME_OVER", level=2)
                else:
                    # Regular input
                    client_inputs[player_id] = data
    except Exception as e:
        logger.error(f"Error in client handler for player {player_id}: {e}")
        vprint(f"[SERVER] Error in handler for Player {player_id + 1}: {e}", level=0)
        logger.info(f"Player {player_id} lost connection (exception)")
        vprint(f"[SERVER] Player {player_id + 1} lost connection (exception)", level=2)
    finally:
        try:
            client_socket.close()
        except:
            pass
        if player_id in clients: 
            del clients[player_id]
        logger.info(f"Player {player_id} disconnected")
        vprint(f"[SERVER] Player {player_id + 1} disconnected", level=1)

def broadcast_state(state: dict):
    """Broadcast game state to all connected clients (non-blocking)."""
    disconnected = []
    for player_id, sock in list(clients.items()):
        try:
            send_data(sock, state)
        except Exception as e:
            logger.warning(f"Failed to send state to player {player_id}: {e}")
            disconnected.append(player_id)
    
    # Clean up disconnected clients
    for player_id in disconnected:
        if player_id in clients:
            try:
                clients[player_id].close()
            except:
                pass
            del clients[player_id]
            logger.info(f"Removed disconnected player {player_id}")

def game_loop():
    """Main simulation loop (60 FPS tick rate for better responsiveness)."""
    vprint("[SERVER] Logic thread started.", level=2)
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
        # Add players to the all_sprites group so their update() method is called
        for p in game.players:
            game.all_sprites.add(p)

        logger.info(f"[SERVER] Created {len(game.players)} player slots (headless mode)")
        vprint(f"[SERVER] Created {len(game.players)} player slots (headless mode)", level=2)

        target_dt = 1.0 / SERVER_FPS
        
        # --- OUTER LOOP: Support multiple game rounds ---
        while not shutdown_event.is_set():
            # --- WAITING PHASE ---
            vprint("[SERVER] Waiting for 2 players to connect...", level=1)
            logger.info("Server is in waiting state.")
            game_start_event.clear()
            game.state = GameState.WAITING_FOR_PLAYERS
            
            waiting_start_time = time.time()
            last_broadcast_time = 0
            
            while not game_start_event.is_set() and not shutdown_event.is_set():
                current_time = time.time()
                
                # Check for timeout
                if current_time - waiting_start_time > WAITING_TIMEOUT:
                    logger.warning("Waiting timeout reached. Resetting server.")
                    vprint("[SERVER] Waiting timeout - no players joined. Resetting...", level=1)
                    # Disconnect any partial connections
                    for player_id in list(clients.keys()):
                        try:
                            clients[player_id].close()
                        except:
                            pass
                        del clients[player_id]
                    waiting_start_time = time.time()
                
                # Broadcast waiting state at faster interval
                if current_time - last_broadcast_time >= WAITING_BROADCAST_INTERVAL:
                    waiting_state = {
                        'players': [], 'enemies': [], 'bullets': [], 'powerups': [],
                        'score': 0, 'coins': 0, 'level': 1, 'time_remaining': 0,
                        'game_state_enum': GameState.WAITING_FOR_PLAYERS.value
                    }
                    broadcast_state(waiting_state)
                    last_broadcast_time = current_time
                
                time.sleep(0.05)  # Small sleep to prevent busy waiting

            # --- GAME PHASE ---
            if shutdown_event.is_set():
                break
                
            vprint("[SERVER] 2/2 players connected. Game starting now!", level=1)
            game.init_game() 
            game.state = GameState.PLAYING 
            logger.info("[SERVER] Game started with 2 players.")
            vprint("[SERVER] Game loop initialized - simulation starting", level=2)
            
            loop_count = 0
            last_bullet_count = 0
            
            # Game loop - play until game over
            while game.state == GameState.PLAYING and not shutdown_event.is_set():
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
                            
                            # Handle shooting
                            if inputs.get('shoot'):
                                bullets = p.shoot()
                                if bullets:
                                    for b in bullets:
                                        game.bullets.add(b)
                                        game.all_sprites.add(b)
                                    vprint(f"[SERVER] Player {p_id + 1} fired {len(bullets)} bullet(s)", level=3)

                    # DETECT PLAYER DISCONNECTION MID-GAME
                    if len(clients) < 2 and game.state == GameState.PLAYING:
                        logger.info(f"Player disconnected mid-game. {len(clients)}/2 remain. Ending game.")
                        game.state = GameState.GAME_OVER
                        vprint(f"[SERVER] A player disconnected. Game ending...", level=1)

                    # CHECK TIMER
                    if game.level and not game.level.update_timer():
                        logger.info("Server-side timer expired. Setting state to GAME_OVER.")
                        game.state = GameState.GAME_OVER

                    # CHECK IF ANY PLAYER HAS DIED
                    for player in game.players:
                        if player.health <= 0 and game.state == GameState.PLAYING:
                            logger.info(f"A player died. Health: {player.health}. Ending game.")
                            game.state = GameState.GAME_OVER
                            vprint(f"[SERVER] A player died. Game over.", level=1)
                            break

                    # Check level completion
                    if (game.level.enemies_spawned >= game.level.enemies_to_spawn and
                        len(game.enemies) == 0 and game.state == GameState.PLAYING):
                        logger.info(f"Level completed! All enemies defeated.")
                        game.state = GameState.LEVEL_COMPLETE
                        vprint(f"[SERVER] Level completed!", level=1)

                    # --- Server-Side Update ---
                    game.all_sprites.update()

                    # Spawn enemies
                    if game.level.should_spawn_enemy() and game.state == GameState.PLAYING:
                        enemy_type = EnemyFactory.get_random_type(game.current_level)
                        enemy = EnemyFactory.create(
                            enemy_type,
                            random.randint(50, game_config.SCREEN_WIDTH - 50),
                            -50,
                            game.current_level
                        )
                        if enemy:
                            game.enemies.add(enemy)
                            game.all_sprites.add(enemy)
                            vprint(f"[SERVER] Enemy spawned: {enemy_type} (Total: {len(game.enemies)})", level=3)

                    # Run collision checks
                    game.update()
                    
                    # Broadcast state to all clients
                    state = get_game_state(game)
                    broadcast_state(state)

                    # Frame timing
                    elapsed = time.perf_counter() - start_time
                    sleep_time = max(0, target_dt - elapsed)
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    
                    loop_count += 1
                    if loop_count % 600 == 0:
                        msg = f"Game loop: {loop_count} ticks, {len(clients)}/2 clients, {len(game.bullets)} bullets, {len(game.enemies)} enemies, L{game.current_level}"
                        logger.info(msg)
                        vprint(f"[SERVER] {msg}", level=2)
                        
                except Exception as e:
                    logger.error(f"Error in game loop: {e}")
                    vprint(f"[SERVER] Game loop error: {e}", level=0)
                    traceback.print_exc()
                    time.sleep(0.05)
            
            # After game ends, send final state
            if not shutdown_event.is_set():
                state = get_game_state(game)
                broadcast_state(state)
                time.sleep(1)  # Brief pause before waiting for next game
    
    except Exception as e:
        logger.critical(f"Fatal error in game_loop: {e}")
        vprint(f"[CRITICAL] Fatal game loop error: {e}", level=0)
        traceback.print_exc()
        shutdown_event.set()

        
def main(argv=None):
    global VERBOSE_LEVEL
    
    if argv is None:
        argv = sys.argv

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Space Defender Multiplayer Server")
    parser.add_argument('port', nargs='?', type=int, default=DEFAULT_PORT,
                        help=f"Port to listen on (default: {DEFAULT_PORT})")
    parser.add_argument('-v', '--verbose', type=int, dest='verbose_level', default=1, choices=[0, 1, 2, 3],
                        help="Verbosity level (0=silent, 1=low, 2=medium, 3=high, default=1)")
    
    # Handle legacy single argument format (just port)
    if len(argv) > 1 and argv[1].isdigit():
        port = int(argv[1])
        VERBOSE_LEVEL = parser.parse_args(argv[2:]).verbose_level if len(argv) > 2 else 1
    else:
        args = parser.parse_args(argv[1:])
        port = args.port
        VERBOSE_LEVEL = args.verbose_level
    
    vprint(f"\n{'='*60}", level=1)
    vprint(f"  SPACE DEFENDER - MULTIPLAYER SERVER (IMPROVED)", level=1)
    vprint(f"{'='*60}", level=1)
    vprint(f"  Host: {HOST}", level=1)
    vprint(f"  Port: {port}", level=1)
    vprint(f"  Max Players: 2", level=1)
    vprint(f"  Tick Rate: {SERVER_FPS} FPS", level=1)
    vprint(f"  Waiting Timeout: {WAITING_TIMEOUT}s", level=1)
    vprint(f"  Verbosity: {VERBOSE_LEVEL} (0=silent, 1=low, 2=med, 3=high)", level=1)
    vprint(f"{'='*60}\n", level=1)
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, port))
        server_socket.listen(2)
        logger.info(f"[SERVER] Listening on {HOST}:{port} (GUI Disabled)")
        vprint(f"[SERVER] Listening on {HOST}:{port}", level=1)
        vprint(f"[SERVER] Waiting for clients to connect...", level=1)
        vprint(f"[SERVER] Press Ctrl+C to stop server\n", level=1)
    except Exception as e:
        logger.critical(f"[CRITICAL] Bind failed: {e}")
        vprint(f"[CRITICAL] Failed to start server: {e}", level=0)
        vprint(f"[CRITICAL] Make sure port {port} is not already in use", level=0)
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
                    vprint(f"[SERVER] ✓ Player {p_id + 1} connected from {addr}", level=1)
                    
                    # Send the client its player id
                    handshake = {'player_id': p_id}
                    send_data(conn, handshake)

                    # Send initial waiting state
                    try:
                        initial_state = {
                            'players': [], 'enemies': [], 'bullets': [], 'powerups': [],
                            'score': 0, 'coins': 0, 'level': 1, 'time_remaining': 0,
                            'game_state_enum': GameState.WAITING_FOR_PLAYERS.value
                        }
                        send_data(conn, initial_state)
                    except Exception:
                        pass

                    # If this is the second player, start the game
                    if len(clients) == 2:
                        logger.info("Two players connected. Setting game start event.")
                        vprint("[SERVER] Two players ready. Starting game...", level=1)
                        game_start_event.set()
                    vprint(f"[SERVER] {len(clients)}/2 players connected", level=1)
                else:
                    conn.close()
                    logger.warning(f"[SERVER] Connection rejected from {addr} - server full")
                    vprint(f"[SERVER] ✗ Connection rejected from {addr} - server full (2/2 players)", level=1)
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"Error accepting connection: {e}")
                continue
    except KeyboardInterrupt:
        logger.info("\n[SERVER] Shutting down on user interrupt...")
        vprint("\n[SERVER] Shutting down...", level=1)
    except Exception as e:
        logger.error(f"Server error: {e}")
        vprint(f"[SERVER] Error: {e}", level=0)
        traceback.print_exc()
    finally:
        shutdown_event.set()
        server_socket.close()
        logger.info("[SERVER] Server shutdown complete")
        vprint("[SERVER] Server shutdown complete", level=1)

if __name__ == "__main__":
    main()