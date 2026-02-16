#!/usr/bin/env python3
"""
Quick Apply Script for Client Improvements
This script applies all client-side improvements to core/game.py
"""

import os
import sys
import re
from pathlib import Path

def backup_file(filepath):
    """Create a backup of the original file"""
    backup_path = f"{filepath}.backup"
    if not os.path.exists(backup_path):
        with open(filepath, 'r') as f:
            content = f.read()
        with open(backup_path, 'w') as f:
            f.write(content)
        print(f"✓ Created backup: {backup_path}")
    else:
        print(f"ℹ Backup already exists: {backup_path}")

def apply_init_changes(content):
    """Add tracking variables to __init__ method"""
    # Find the __init__ method and add new variables
    init_pattern = r"(def __init__\(self.*?\):.*?self\.server_port = \d+)"
    
    new_vars = """
        
        # Network performance tracking
        self.waiting_start_time = None
        self.last_state_time = time.time()
        self.missed_updates = 0"""
    
    if "self.waiting_start_time" not in content:
        content = re.sub(init_pattern, r"\1" + new_vars, content, flags=re.DOTALL)
        print("✓ Added network tracking variables to __init__")
    else:
        print("ℹ Network tracking variables already present")
    
    return content

def apply_timeout_change(content):
    """Change socket timeout from 0.1 to 0.05"""
    old_timeout = "self.server_socket.settimeout(0.1)"
    new_timeout = "self.server_socket.settimeout(0.05)  # 50ms for faster updates"
    
    if old_timeout in content:
        content = content.replace(old_timeout, new_timeout)
        print("✓ Updated socket timeout to 50ms")
    elif "self.server_socket.settimeout(0.05)" in content:
        print("ℹ Socket timeout already set to 50ms")
    else:
        print("⚠ Could not find socket timeout to update")
    
    return content

def create_improved_network_block():
    """Return the improved network client logic block"""
    return '''        # --- NETWORK CLIENT LOGIC (IMPROVED) ---
        if self.is_network_mode and self.state in (GameState.PLAYING, GameState.WAITING_FOR_PLAYERS):
            # Track waiting timeout protection
            if self.state == GameState.WAITING_FOR_PLAYERS:
                if self.waiting_start_time is None:
                    self.waiting_start_time = time.time()
                    logger.info("Entered waiting state, timeout tracking started")
                elif time.time() - self.waiting_start_time > 60:  # 60 second timeout
                    logger.warning("Waiting timeout exceeded - returning to main menu")
                    self.is_network_mode = False
                    self.state = GameState.MAIN_MENU
                    if self.server_socket:
                        try:
                            self.server_socket.close()
                        except:
                            pass
                        self.server_socket = None
                    return
            else:
                self.waiting_start_time = None  # Reset when not waiting

            # Play background music on first frame
            if self.state == GameState.PLAYING and not self.background_music_playing:
                if self.assets:
                    self.assets.play_sound('splash', 0.2)
                self.background_music_playing = True

            # 1. Send local input to server
            keys = pygame.key.get_pressed()
            mouse_buttons = pygame.mouse.get_pressed()
            input_payload = {'keys': [], 'shoot': False}
            
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                input_payload['keys'].append('a')
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                input_payload['keys'].append('d')
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                input_payload['keys'].append('w')
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                input_payload['keys'].append('s')
            if keys[pygame.K_SPACE] or mouse_buttons[0]:
                input_payload['shoot'] = True

            try:
                send_data(self.server_socket, input_payload)
            except ConnectionResetError:
                logger.error("Connection lost to server")
                self.is_network_mode = False
                self.state = GameState.MAIN_MENU
                if self.server_socket:
                    try:
                        self.server_socket.close()
                    except:
                        pass
                    self.server_socket = None
                return
            except Exception as e:
                logger.debug(f"Failed to send input (non-fatal): {e}")

            # 2. Receive game state from server (catch-up mechanism)
            states_received = 0
            max_states_per_frame = 3  # Process up to 3 states to catch up
            
            while states_received < max_states_per_frame:
                try:
                    received_state = receive_data(self.server_socket)
                    if received_state is not None:
                        states_received += 1
                        self.last_state_time = time.time()
                        self.missed_updates = 0
                        
                        # Process server state enum
                        enum_val = received_state.get('game_state_enum')
                        if isinstance(enum_val, int):
                            try:
                                server_state = GameState(enum_val)
                                if server_state == GameState.PLAYING and self.state == GameState.WAITING_FOR_PLAYERS:
                                    logger.info("Server state=PLAYING — switching client to PLAYING")
                                    self.state = GameState.PLAYING
                                elif server_state == GameState.WAITING_FOR_PLAYERS:
                                    self.state = GameState.WAITING_FOR_PLAYERS
                                elif server_state == GameState.GAME_OVER and self.state == GameState.PLAYING:
                                    logger.info("Server state=GAME_OVER — switching client to GAME_OVER")
                                    self.state = GameState.GAME_OVER
                            except Exception:
                                pass

                        self.game_state_from_server = received_state
                    else:
                        break
                except socket.timeout:
                    break
                except Exception as e:
                    logger.debug(f"Receive error (non-fatal): {e}")
                    break

            # Track connection health
            if states_received == 0:
                self.missed_updates += 1
                if self.missed_updates > 180:  # 6 seconds at 30 FPS
                    logger.error("No server updates for 6 seconds - connection lost")
                    self.is_network_mode = False
                    self.state = GameState.MAIN_MENU
                    if self.server_socket:
                        try:
                            self.server_socket.close()
                        except:
                            pass
                        self.server_socket = None
                    return

            # 3. Apply server state
            if self.game_state_from_server:
                self.apply_server_state(self.game_state_from_server)

            # Update sprites and particles
            self.all_sprites.update()
            if self.particle_system:
                self.particle_system.update()

            self.update_starfield()
            return'''

def apply_network_improvements(content):
    """Replace network client logic with improved version"""
    # This is complex - look for the network mode block and replace it
    # Pattern: from "if self.is_network_mode" to "return" before "# --- LOCAL SIMULATION"
    
    if "# Track waiting timeout protection" in content:
        print("ℹ Network improvements already applied")
        return content
    
    # Find the network block - it's between these markers
    start_marker = "        # --- NETWORK CLIENT LOGIC ---"
    end_marker = "        # --- LOCAL SIMULATION LOGIC"
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        print("⚠ Could not locate network client logic block")
        print("   You may need to apply this change manually")
        return content
    
    # Replace the block
    new_block = create_improved_network_block()
    content = content[:start_idx] + new_block + "\n\n" + content[end_idx:]
    print("✓ Applied improved network client logic")
    
    return content

def main():
    print("="*60)
    print("Space Defender - Client Improvement Patcher")
    print("="*60)
    print()
    
    # Find core/game.py
    game_file = Path("core/game.py")
    if not game_file.exists():
        print("❌ Error: core/game.py not found")
        print("   Make sure you're running this from the project root")
        sys.exit(1)
    
    print(f"Found: {game_file}")
    print()
    
    # Backup original
    print("Step 1: Creating backup...")
    backup_file(str(game_file))
    print()
    
    # Read file
    print("Step 2: Reading current file...")
    with open(game_file, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"✓ Read {len(content)} characters")
    print()
    
    # Apply changes
    print("Step 3: Applying improvements...")
    content = apply_init_changes(content)
    content = apply_timeout_change(content)
    content = apply_network_improvements(content)
    print()
    
    # Write back
    print("Step 4: Writing improved file...")
    with open(game_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ Wrote improved version")
    print()
    
    print("="*60)
    print("✅ CLIENT IMPROVEMENTS APPLIED SUCCESSFULLY!")
    print("="*60)
    print()
    print("Next steps:")
    print("  1. Test the changes: python main.py")
    print("  2. Start improved server: python server_improved.py 35555")
    print("  3. Connect clients and test multiplayer")
    print()
    print("To restore original:")
    print("  cp core/game.py.backup core/game.py")
    print()

if __name__ == "__main__":
    main()
