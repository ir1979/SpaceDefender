"""
Networking Module
Handles sending and receiving JSON-serializable data over sockets.
Supports both blocking (server) and timeout-based non-blocking (client) modes.
"""
import socket
import json
import time
from typing import Optional, Tuple

HEADER_SIZE = 10

# Default server values
DEFAULT_SERVER_HOST = '127.0.0.1'
DEFAULT_SERVER_PORT = 35555

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


def test_connection(host: str, port: int, timeout: float = 3.0) -> Tuple[bool, str]:
    """
    Test connectivity to a server.
    Returns (success: bool, message: str)
    """
    test_socket = None
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(timeout)
        
        start_time = time.time()
        test_socket.connect((host, port))
        connect_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Send a ping message
        ping_data = {'type': 'ping', 'timestamp': time.time()}
        send_data(test_socket, ping_data)
        
        # Try to receive a response
        test_socket.settimeout(timeout)
        response = receive_data(test_socket)
        
        if response and response.get('type') == 'pong':
            return True, f"Connected! Response time: {connect_time:.0f}ms"
        else:
            return True, f"Connected! (Server responded but ping not acknowledged)"
            
    except socket.timeout:
        return False, "Connection timed out"
    except ConnectionRefusedError:
        return False, "Connection refused - server not running"
    except socket.gaierror:
        return False, "Invalid hostname or IP address"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"
    finally:
        if test_socket:
            try:
                test_socket.close()
            except:
                pass
