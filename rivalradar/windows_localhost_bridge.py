"""
Windows localhost TCP bridge for WSL-hosted backend.

Run on Windows side:
- Listens on 127.0.0.1:<listen_port>
- Forwards traffic to <target_host>:<target_port>
"""

import argparse
import socket
import threading


BUFFER_SIZE = 65536


def _copy_stream(src: socket.socket, dst: socket.socket) -> None:
    """Copy bytes from src to dst until src closes, then half-close dst."""
    try:
        while True:
            data = src.recv(BUFFER_SIZE)
            if not data:
                break
            dst.sendall(data)
    except OSError:
        pass
    finally:
        try:
            dst.shutdown(socket.SHUT_WR)
        except OSError:
            pass


def handle_client(client_sock: socket.socket, target_host: str, target_port: int) -> None:
    try:
        upstream_sock = socket.create_connection((target_host, target_port), timeout=10)
    except OSError:
        try:
            client_sock.close()
        except OSError:
            pass
        return

    t1 = threading.Thread(target=_copy_stream, args=(client_sock, upstream_sock), daemon=True)
    t2 = threading.Thread(target=_copy_stream, args=(upstream_sock, client_sock), daemon=True)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    try:
        client_sock.close()
    except OSError:
        pass
    try:
        upstream_sock.close()
    except OSError:
        pass


def run_bridge(listen_host: str, listen_port: int, target_host: str, target_port: int) -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((listen_host, listen_port))
    server.listen(100)

    try:
        while True:
            client_sock, _ = server.accept()
            t = threading.Thread(
                target=handle_client,
                args=(client_sock, target_host, target_port),
                daemon=True,
            )
            t.start()
    finally:
        server.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Windows localhost TCP bridge for WSL")
    parser.add_argument("--listen-host", default="127.0.0.1")
    parser.add_argument("--listen-port", type=int, default=8000)
    parser.add_argument("--target-host", required=True)
    parser.add_argument("--target-port", type=int, default=8000)
    args = parser.parse_args()

    run_bridge(args.listen_host, args.listen_port, args.target_host, args.target_port)


if __name__ == "__main__":
    main()