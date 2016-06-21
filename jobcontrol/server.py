#!/usr/bin/env python3
import logging
import socket
import time

import eventlet

eventlet.monkey_patch()


def printf(format_string, *args):
    print(format_string % args, flush=True)


def _read_until_newline(sock, *, chunk_size=4096):
    buf = b""
    while not buf.endswith(b"\n"):
        buf += sock.recv(chunk_size)
    if buf.count(b"\n") > 1:
        raise ValueError("Recieved more than one line of input!")
    return buf.decode("utf-8")[:-1]



class JobControlServer:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG if __debug__ else logging.INFO)

    def __init__(self, host, port):
        printf("Listening on %s:%s", host, port)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((host, port))
        self._sock.listen(5)
        self.queue = eventlet.queue.PriorityQueue()

    def _send(self, sock, data):
        if not isinstance(data, bytes):
            data = data.encode("utf-8")
        if not data.endswith(b"\n"):
            data += b"\n"
        sock.sendall(data)

    def _handle_client(self, client, address):
        printf("Connected from %s:%s", *address)
        command, *args = _read_until_newline(client).split()
        printf("Got command %r with args %r from %s:%s",
               command, args, *address)
        if command.upper() == "ENQUEUE":
            delay, method_name = args
            delay = int(delay)
            printf("Queueing %r with delay %d second%s from %s:%s",
                   method_name, delay, "s" if delay != 1 else "", *address)
            self.queue.put((time.time() + delay, method_name))
        elif command.upper() == "POP":
            printf("Need to reply to %s:%s with function", *address)
            target_time, method_name = self.queue.get()
            real_delay = max(0, target_time - time.time())
            printf("Got function %r for %s:%s, but need to sleep %.2f seconds",
                   method_name, *address, real_delay)
            eventlet.sleep(real_delay)
            printf("Sending function %r to %s:%s!", method_name, *address)
            self._send(client, method_name)
            self.queue.task_done()
        else:
            raise RuntimeError("Invalid COMMAND {!r}!".format(command))

        client.close()
        printf("Disconnected from %s:%s", *address)

    def mainloop(self):
        while True:
            eventlet.spawn_n(self._handle_client, *self._sock.accept())


def main():
    logging.basicConfig(level=logging.DEBUG)
    jcs = JobControlServer("127.0.0.1", 8080)
    jcs.mainloop()

if __name__ == "__main__":
    main()
