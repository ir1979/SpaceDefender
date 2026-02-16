#!/usr/bin/env python3
"""Test client connection"""
import sys
import os

# Add project root to path (go up 3 directories from test file)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("Testing client mode detection and connection...")

# Simulate the command line
sys.argv = ['main.py', '--host', '127.0.0.1', '--port', '35566']

import argparse
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
    
    print(f"  mode is None, host_specified={host_specified}, port_specified={port_specified}")
    
    if host_specified or port_specified:
        args.mode = 'client'
    else:
        args.mode = 'game'

print(f"Detected mode: {args.mode}")
print(f"Host: {args.host}")
print(f"Port: {args.port}")

if args.mode == 'client':
    print("\nTesting connection to server...")
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)  # 3 second timeout
        print(f"  Attempting to connect to {args.host}:{args.port}...")
        sock.connect((args.host, args.port))
        print("  ✓ Connected successfully!")
        sock.close()
    except ConnectionRefusedError as e:
        print(f"  ✗ Connection refused: {e}")
    except socket.timeout:
        print(f"  ✗ Connection timed out")
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
