#!/usr/bin/env python3
import shutil
import socket
import os
import threading
import typing as t

Socket = socket.SocketType


def recv_lines(client: Socket, *, eol=b"\r\n") -> t.List[str]:
    buf = b""
    while eol not in buf:
        buf += client.recv(4096)
    return [line.decode("utf-8") for line in buf.split(eol)]


def recv_n_lines(client: Socket, amount: int, *, eol=b"\r\n") -> t.List[str]:
    lines = []
    while len(lines) < amount:
        lines.extend(recv_lines(client, eol=eol))
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


def create_header_string(headers: t.Mapping[str, str]) -> bytes:
    header_string = []
    for key, value in headers.items():
        # Sadly, `bytes.format` is not a thing.
        header_string.append(b"%s: %s" % (key.encode("utf-8"),
                                          value.encode("utf-8")))
    return b"\r\n".join(header_string) + b"\r\n"


def send_status(client: Socket, status_code: int):
    client.sendall({
        200: "HTTP/1.1 200 OK",
        400: "HTTP/1.1 400 Bad Request",
    }[status_code].encode("utf-8") + b"\r\n")


def handle_client(page: str, client: Socket, address: t.Tuple[str, str]):
    _ = address
    conn_info, *header_lines = recv_lines(client)
    method, path, html_version = conn_info.split()

    assert method == "GET"
    assert path == "/"
    assert html_version == "HTTP/1.1"
    headers = translate_headers(header_lines)

    filesize = os.path.getsize(page)

    send_status(client, 200)
    client.sendall(create_header_string({
        "Content-Length": str(filesize),
    }))
    client.sendall(b"\r\n")

    with open(page, "rb") as page_file:
        shutil.copyfileobj(page_file, client.makefile("wb"))

    client.sendall(b"\r\n")
    client.close()

def main_server(page: str, host: str = "localhost", port: int = 8080):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(1)
    while True:
        client, address = server.accept()
        threading.Thread(target=handle_client,
                         args=(page, client, address)).start()


def main():
    import sys

    try:
        page = sys.argv[1]
    except IndexError:
        print("USAGE: webserver.py FILENAME")
        sys.exit(1)
    else:
        main_server(page)

if __name__ == "__main__":
    main()
