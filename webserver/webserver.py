#!/usr/bin/env python3
import logging
import mimetypes
import os
import shutil
import socket
import threading
import typing as t

from coroutines import EventLoop

Socket = socket.SocketType
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if __debug__ else logging.INFO)
logging.basicConfig(format="[%(asctime)s %(levelname)s]: %(message)s",
                    datefmt="%H:%M:%S")


def recv_lines(client: Socket, *, eol=b"\r\n") -> t.List[str]:
    buf = b""
    while eol not in buf:
        yield "recv", client
        buf += client.recv(4096)
    return [line.decode("utf-8") for line in buf.split(eol)]


def translate_headers(header_lines: t.Iterable[str]) -> t.Mapping[str, str]:
    headers = {}  # type: t.Mapping[str, str]
    for line in header_lines:
        if not line:
            break
        key, value = line.split(": ", 1)
        # We don't just set the key to the value because, at weird times,
        # browsers send headers multiple times and we have to merge them
        # together, or at least that's what I read ont he internet that one
        # time.
        headers.setdefault(key, "")
        headers[key] += value
    return headers


def send_headers(client: Socket, status_code: int,
                 headers: t.Mapping[str, str] = {}, *, mark_end: bool = True):

    yield "send", client
    client.sendall({
        200: "HTTP/1.1 200 OK",
        400: "HTTP/1.1 400 Bad Request",
    }[status_code].encode("utf-8") + b"\r\n")
    header_string = []
    for key, value in headers.items():
        # Sadly, `bytes.format` is not a thing.
        header_string.append(b"%s: %s" % (key.encode("utf-8"),
                                          value.encode("utf-8")))
    yield "send", client
    client.sendall(b"\r\n".join(header_string) + b"\r\n")
    if mark_end:
        yield "send", client
        client.sendall(b"\r\n")


def send_file(client: Socket, filename: str):
    with open(filename, "rb") as fileobj:
        while True:
            chunk = fileobj.read(4096)
            if not chunk:
                break
            yield "send", client
            client.sendall(chunk)


def handle_client(page: str, client: Socket, address: t.Tuple[str, str]):
    logger.info("Connected from %s:%s", *address)
    conn_info, *header_lines = yield from recv_lines(client)
    try:
        method, path, html_version = conn_info.split()
        assert method == "GET"
        assert path == "/"
        assert html_version == "HTTP/1.1"
    except (ValueError, AssertionError):
        logger.info("Got invalid request from %s:%s!", *address)
        yield from send_headers(client, 400)
    else:
        headers = translate_headers(header_lines)
        logger.info("Recieved headers %s from %s:%s", headers, *address)
        filesize = os.path.getsize(page)
        mimetype, encoding = mimetypes.guess_type(page)
        logger.info("Sending headers to %s:%s", *address)
        yield from send_headers(client, 200, {
            "Content-Length": str(filesize),
            "Content-Type": mimetype or "",
            "Content-Encoding": encoding or "",
        }, mark_end=True)
        logger.info("Sending file to %s:%s", *address)
        yield from send_file(client, page)

    logger.info("Done with %s:%s", *address)
    yield "send", client
    client.sendall(b"\r\n")
    client.close()
    logger.info("Disconnected from {}:{}".format(*address))


def main_server(page: str, host: str = "localhost", port: int = 8080):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(1)
    logger.info("Starting server")
    while True:
        yield "recv", server
        client, address = server.accept()
        yield "new_coroutine", handle_client, (page, client, address), {}


def main():
    import sys

    socket.setdefaulttimeout(0)
    el = EventLoop()

    try:
        page = sys.argv[1]
    except IndexError:
        print("USAGE: webserver.py FILENAME")
        sys.exit(1)
    else:
        el.start_new_coroutine(main_server, (page,))
        el.mainloop()

if __name__ == "__main__":
    main()
