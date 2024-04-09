import socket
import pickle
import re
import sys

port_pattern = r"^[0-9]{1,5}$"


def check_address(addr: tuple) -> bool:
    host, port = addr
    return (
        isinstance(addr, tuple)
        and isinstance(port, int)
        and re.match(port_pattern, str(port))
        and isinstance(host, str)
        and host
    )


class Client:
    def __init__(self, *, bind_addr: tuple) -> None:

        if check_address(bind_addr):
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind(bind_addr)

    def send_object(self, addr: tuple, obj) -> None:

        if isinstance(addr, tuple):
            self.socket.connect(addr)

            # Send size
            obj_size = str(sys.getsizeof(obj)).encode()
            self.socket.sendall(obj_size)

            # Send obj
            self.socket.sendall(pickle.dump(obj))

            self.socket.close()  # Reset socket

    def recv_obj(self, addr: tuple) -> None | object:
        if check_address(addr):
            self.socket.listen()
            conn, _ = self.socket.accept()

            # Receive size
            obj_size = int(conn.recv(1024).decode())

            # Receive object
            received_obj = b""
            while len(received_obj) < obj_size:
                chunk_size = min(obj_size - len(received_obj), 1024)
                chunk = conn.recv()
                if not chunk:
                    break
                received_obj += chunk

            conn.close()

            return pickle.loads(received_obj)

    # Context managing protocol

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        self.socket.close()
        return False  # let the user handle any exception
