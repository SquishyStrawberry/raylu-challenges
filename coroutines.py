#!/usr/bin/env python3
import select
import typing as t


class EventLoop:
    def __init__(self):
        self.doing_nothing = []
        self.recv_wait = {}
        self.send_wait = {}

    def start_new_coroutine(self, func, args=(), kwargs={}):
        self.doing_nothing.append(func(*args, **kwargs))

    def _tick(self):
        if self.recv_wait or self.send_wait:
            recv_ready, send_ready, [] = \
                select.select(self.recv_wait.keys(), self.send_wait.keys(), [])

            for sock in recv_ready:
                self.doing_nothing.append(self.recv_wait.pop(sock))

            for sock in send_ready:
                self.doing_nothing.append(self.send_wait.pop(sock))

        for coroutine in tuple(self.doing_nothing):
            why, what, *extra = next(coroutine)
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
