#!/usr/bin/env python3
import mimetypes
import os
import shutil
import socket
import threading
import typing as t

from coroutines import EventLoop

Socket = socket.SocketType


def recv_lines(client: Socket, *, eol=b"\r\n") -> t.List[str]:
    buf = b""
    while eol not in buf:
        yield "recv", client
        buf += client.recv(4096)
    return [line.decode("utf-8") for line in buf.split(eol)]


def recv_n_lines(client: Socket, amount: int, *, eol=b"\r\n") -> t.List[str]:
    lines = []
    while len(lines) < amount:
        new_lines = yield from recv_lines(client, eol=eol)
        lines.extend(new_lines)
    return lines


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
            yield "send", client
            client.sendall(chunk)


def handle_client(page: str, client: Socket, address: t.Tuple[str, str]):
    conn_info, *header_lines = yield from recv_lines(client)
    method, path, html_version = conn_info.split()
    try:
        assert method == "GET"
        assert path == "/"
        assert html_version == "HTTP/1.1"
    except AssertionError:
        yield from send_headers(client, 400)
    else:
        _ = translate_headers(header_lines)
        filesize = os.path.getsize(page)
        mimetype, encoding = mimetypes.guess_type(page)
        yield from send_headers(client, 200, {
            "Content-Length": str(filesize),
            "Content-Type": mimetype or "",
            "Content-Encoding": encoding or "",
        }, mark_end=True)
        yield from send_file(client, page)

    yield "send", client
    client.sendall(b"\r\n")
    client.close()


def main_server(page: str, host: str = "localhost", port: int = 8080):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(1)
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
