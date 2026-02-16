import socket
import threading
import time

# Import the networking module directly (avoid importing the entire `systems` package
# which may initialize pygame in this test environment).
import importlib.util
from pathlib import Path
network_path = Path(__file__).resolve().parent / 'systems' / 'network.py'
spec = importlib.util.spec_from_file_location('systems_network', network_path)
network = importlib.util.module_from_spec(spec)
spec.loader.exec_module(network)
send_data = network.send_data
receive_data = network.receive_data


def _server_worker(listener, result_container):
    conn, _ = listener.accept()
    try:
        msg = receive_data(conn)
        result_container['received'] = msg
        # echo back
        send_data(conn, {'ack': True, 'original': msg})
    finally:
        conn.close()


def test_send_receive_roundtrip():
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(('127.0.0.1', 0))
    listener.listen(1)
    port = listener.getsockname()[1]

    result = {}
    t = threading.Thread(target=_server_worker, args=(listener, result), daemon=True)
    t.start()

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', port))

    payload = {'numbers': list(range(1000)), 'text': 'x' * 5000}
    send_data(client, payload)

    # server should echo back
    resp = receive_data(client)
    client.close()
    listener.close()

    assert resp is not None
    assert resp.get('ack') is True
    assert resp.get('original') == payload
    assert result.get('received') == payload