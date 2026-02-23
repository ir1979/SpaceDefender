"""
Networking Module
Handles sending and receiving JSON-serializable data over sockets.
Supports both blocking (server) and timeout-based non-blocking (client) modes.
"""
import socket
import json
from typing import Optional

HEADER_SIZE = 10

def send_data(client_socket: socket.socket, data: dict):
    """
    Serializes data to JSON, prefixes it with a fixed-size header
    indicating the message length, and sends it.
    """
    try:
        msg = json.dumps(data).encode('utf-8')
        header = f"{len(msg):<{HEADER_SIZE}}".encode('utf-8')
        client_socket.sendall(header + msg)
    except (ConnectionResetError, BrokenPipeError):
        # Handle cases where the client has disconnected
        pass
    except Exception as e:
        print(f"[NETWORK] Error sending data: {e}")

def receive_data(client_socket: socket.socket) -> Optional[dict]:
    """
    Receives data by first reading the fixed-size header and then reading
    the exact number of bytes for the message. Uses a loop to ensure the
    full payload is received even when socket.recv() returns partial data.
    Returns None on disconnect, malformed messages, or timeout (no data ready).
    """
    try:
        header = client_socket.recv(HEADER_SIZE)
        if not header or len(header.strip()) == 0:
            return None

        try:
            msg_len = int(header.decode('utf-8').strip())
        except ValueError:
            return None

        # Read the full message in a loop (recv may return partial data)
        chunks = []
        bytes_recd = 0
        while bytes_recd < msg_len:
            chunk = client_socket.recv(min(4096, msg_len - bytes_recd))
            if not chunk:
                # Peer closed connection
                return None
            chunks.append(chunk)
            bytes_recd += len(chunk)

        full_msg = b''.join(chunks)
        return json.loads(full_msg.decode('utf-8'))
    except socket.timeout:
        # Timeout: no data available (normal with non-blocking mode)
        return None
    except (ConnectionResetError, json.JSONDecodeError, BrokenPipeError):
        # Handle client disconnection or corrupted data
        return None