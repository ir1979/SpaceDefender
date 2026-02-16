#!/usr/bin/env python3
"""
Server Integration Test

This test validates the core functionality of the authoritative server:
1. Starts the server in a background thread.
2. Simulates a client connecting to the server.
3. Sends mock user inputs (e.g., movement, shooting) to the server.
4. Receives game state updates from the server.
5. Validates the structure and content of the received game state.
6. Gracefully shuts down the client and server.
"""

import socket
import threading
import time
import unittest
import sys

# Add project root to path to allow imports
sys.path.insert(0, '.')

from server import main as server_main, shutdown_event, DEFAULT_PORT
from systems.network import send_data, receive_data
from systems.logger import setup_logging

# Initialize logging for the test
logger = setup_logging()

HOST = '127.0.0.1'

class TestServerIntegration(unittest.TestCase):
    """Test suite for the game server."""

    @classmethod
    def setUpClass(cls):
        """Set up the test environment by starting the server."""
        logger.info("="*80)
        logger.info("Setting up server test environment...")
        
        # To run the server's main function, we need to simulate command-line args
        # We pass the port number as a string, just like sys.argv would.
        server_args = [sys.argv[0], str(DEFAULT_PORT)]
        
        cls.server_thread = threading.Thread(
            target=server_main, 
            args=(server_args,), # Pass the list as the single argument to main
            daemon=True
        )
        cls.server_thread.start()
        logger.info(f"Server thread started. Waiting for it to initialize...")
        time.sleep(2)  # Give the server a moment to bind and start listening

    @classmethod
    def tearDownClass(cls):
        """Clean up the test environment by shutting down the server."""
        logger.info("Tearing down server test environment...")
        shutdown_event.set()
        cls.server_thread.join(timeout=3)
        if cls.server_thread.is_alive():
            logger.warning("Server thread did not shut down cleanly.")
        else:
            logger.info("Server thread shut down successfully.")
        logger.info("="*80)

    def test_client_connection_and_communication(self):
        """Tests a single client connecting, sending input, and receiving state."""
        logger.info("--- Running test: test_client_connection_and_communication ---")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((HOST, DEFAULT_PORT))
                logger.info(f"✓ Mock client connected to server at {HOST}:{DEFAULT_PORT}")

                # Simulate a few frames of interaction
                for i in range(5):
                    input_payload = {'keys': ['d'], 'shoot': i % 2 == 0} # Move right, shoot every other frame
                    send_data(client_socket, input_payload)

                    state = receive_data(client_socket)
                    self.assertIsNotNone(state, "Server did not send a state update.")
                    self.assertIsInstance(state, dict, "State from server is not a dictionary.")
                    
                    # Validate the structure of the received state
                    self.assertIn('players', state)
                    self.assertIn('enemies', state)
                    self.assertIn('bullets', state)
                    logger.info(f"✓ Received and validated game state for frame {i+1}")

        except ConnectionRefusedError:
            self.fail("Server connection refused. The server may not have started correctly.")
        except Exception as e:
            self.fail(f"An unexpected error occurred during the test: {e}")

if __name__ == '__main__':
    unittest.main()