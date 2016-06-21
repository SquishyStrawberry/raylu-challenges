#!/usr/bin/env python3
import socket


class JobScheduler:
    def __init__(self, host, port):
        self._sock = socket.socket()
        self._sock.connect((host, port))

    def enqueue(self, function, delay=0):
        if callable(function):
            name = function.__name__
        elif isinstance(function, str):
            name = function
        else:
            raise ValueError("Invalid argument!")
        self._sock.sendall("ENQUEUE {} {}\n".format(delay, name).encode("utf-8"))
