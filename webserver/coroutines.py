#!/usr/bin/env python3
import select
import logging

__all__ = ["EventLoop", "AsyncSocket"]
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if __debug__ else logging.INFO)


class EventLoop:
    def __init__(self):
        self.doing_nothing = []
        self.recv_wait = {}
        self.send_wait = {}

    def start_new_coroutine(self, func, args=(), kwargs={}):
        self.doing_nothing.append(func(*args, **kwargs))

    def _tick(self):
        recv_ready, send_ready, [] = \
            select.select(self.recv_wait.keys(), self.send_wait.keys(), [],
                         0 if self.doing_nothing else None)

        for sock in recv_ready:
            self.doing_nothing.append(self.recv_wait.pop(sock))

        for sock in send_ready:
            self.doing_nothing.append(self.send_wait.pop(sock))

        logger.debug("Coroutines %s are doing nothing",
                     [f.__name__ for f in self.doing_nothing])
        for coroutine in tuple(self.doing_nothing):
            try:
                why, what, *extra = next(coroutine)
            except StopIteration:
                logger.debug("%s is done running", coroutine.__name__)
                self.doing_nothing.remove(coroutine)
                continue
            logger.debug("%s is trying to %s", coroutine.__name__, why)
            if why == "recv":
                self.doing_nothing.remove(coroutine)
                self.recv_wait[what] = coroutine
            elif why == "send":
                self.doing_nothing.remove(coroutine)
                self.send_wait[what] = coroutine
            elif why == "new_coroutine":
                args, kwargs = extra
                self.start_new_coroutine(what, args, kwargs)
            else:
                raise RuntimeError("Invalid coroutine action!")

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
