#!/usr/bin/env python3
import select
import logging

__all__ = ["EventLoop", "AsyncSocket"]
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if __debug__ else logging.INFO)


class EventLoop:
    def __init__(self):
        self.recv_wait = {}
        self.send_wait = {}

    def start(self, func, *args, **kwargs):
        self._step_coroutine(func(*args, **kwargs))

    def _step_coroutine(self, coroutine):
        try:
            why, what, *extra = next(coroutine)
        except StopIteration:
            logger.debug("%s is done running", coroutine.__name__)
            return
        logger.debug("%s is trying to %s", coroutine.__name__, why)
        if why == "recv":
            self.recv_wait[what] = coroutine
        elif why == "send":
            self.send_wait[what] = coroutine
        elif why == "start_coroutine":
            try:
                args, kwargs = extra
            except ValueError:
                kwargs = {}
                try:
                    [args] = extra
                except ValueError:
                    args = ()
            self.start(what, *args, **kwargs)
            self._step_coroutine(coroutine)
        else:
            raise RuntimeError("Invalid coroutine action!")

    def _tick(self):
        recv_ready, send_ready, [] = \
            select.select(self.recv_wait.keys(), self.send_wait.keys(), [])

        for sock in recv_ready:
            self._step_coroutine(self.recv_wait.pop(sock))

        for sock in send_ready:
            self._step_coroutine(self.send_wait.pop(sock))

    def mainloop(self):
        while True:
            self._tick()


class AsyncSocket:
    def __init__(self, sock: "socket.SocketType"):
        self._sock = sock

    def recv(self, bufsize, flags=0):
        yield "recv", self._sock
        return self._sock.recv(bufsize, flags)

    def send(self, bytes_, flags=0):
        yield "send", self._sock
        return self._sock.send(bytes_, flags)

    def sendall(self, bytes_, flags=0):
        remaining = bytes_
        while remaining:
            sent = yield from self.send(remaining, flags)
            remaining = remaining[sent:]

    def accept(self, *, convert_to_async_socket=True):
        yield "recv", self._sock
        conn, addr = self._sock.accept()
        if convert_to_async_socket:
            return self.__class__(conn), addr
        else:
            return conn, addr

    def __getattr__(self, key):
        return getattr(self._sock, key)
