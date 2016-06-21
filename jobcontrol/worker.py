#!/usr/bin/env python3
import argparse
import socket

import codebase


def printf(format_string, *args):
    print(format_string % args, flush=True)


def worker(host, port, module):
    printf("Using address %s:%s and module %r", host, port, module)
    while True:
        sock = socket.socket()
        sock.connect((host, port))
        printf("Trying to get function...")
        sock.sendall(b"POP\n")
        name = sock.recv(4096).strip()
        printf("Got function %r", name)
        getattr(module, name)()


def main():
    argp = argparse.ArgumentParser("worker.py")

    argp.add_argument("host",
                      help="The host of the JobControlServer.")
    argp.add_argument("port", type=int,
                      help="The port of the JobControlServer.")

    argv = argp.parse_args()
    worker(argv.host, argv.port, codebase)

if __name__ == "__main__":
    main()
