import socket
import pickle
import re
import sys
from time import sleep


class ObjectReceiveError(Exception):
    """Raised when the obj is not received properly."""

    __str__ = lambda _: "Couldn't Receive Object properly"


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


def get_tcp_sock():
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)


class Client:
    def __init__(self, bind_addr: tuple) -> None:

        if check_address(bind_addr):
            self.bind_addr = bind_addr
            self.socket = get_tcp_sock()

    def send_object(self, addr: tuple, obj) -> None:

        if isinstance(addr, tuple):
            while True:
                try:
                    self.socket.connect(addr)
                    break
                except ConnectionRefusedError:
                    continue
            try:
                # Send size
                obj_size = sys.getsizeof(obj).to_bytes(8, byteorder="big")
                self.socket.sendall(obj_size)

                # Send obj
                self.socket.sendall(pickle.dumps(obj) + b"EOF")
                sleep(0.15)  # A small delay to address race conditions

            finally:
                # Reset socket
                self.socket.close()
                self.socket = get_tcp_sock()

    def recv_obj(self, addr: tuple) -> None | object:
        if check_address():
            try:
                self.socket.bind(self.bind_addr)
                self.socket.listen()
                conn, _ = self.socket.accept()

                # Receive size
                obj_size = int.from_bytes(conn.recv(8), "big")

                # Receive object
                received_obj = b""
                while len(received_obj) < obj_size:
                    chunk_size = min(obj_size - len(received_obj), 1024)
                    chunk = conn.recv(chunk_size)
                    if not chunk and received_obj.endswith(b"EOF"):
                        break
                    received_obj += chunk

                if received_obj.endswith(b"EOF"):
                    received_obj = received_obj[:-3]

                else:
                    raise ObjectReceiveError()

                conn.close()
                return pickle.loads(received_obj)

            finally:
                # Reset the socket
                self.socket.close()
                self.socket = get_tcp_sock()

    # Context managing protocol
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        self.socket.close()
        return False  # let the user handle any exception
