#!/usr/bin/env python3
import socket
import typing as t

from pprint import pprint  # TODO Remove this.

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


def send_status(client: Socket, status_code: int):
    client.send({
        200: "HTTP/1.1 200 OK",
        400: "HTTP/1.1 400 Bad Request",
    }[status_code].encode("utf-8") + b"\r\n")


def main_server(host="localhost", port=8080):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(1)
    while True:
        client, _ = server.accept()
        conn_info, *header_lines = recv_lines(client)
        method, path, html_version = conn_info.split()
        try:
            assert method == "GET"
            assert path == "/"
            assert html_version == "HTTP/1.1"
        except AssertionError:
            send_status(client, 400)
        else:
            _ = translate_headers(header_lines)
            send_status(client, 200)
            client.sendall(b"\r\n\r\n")
            client.sendall(b"<html>"
                           b"<head>"
                           b"<title>Test Title!</title>"
                           b"</head>"
                           b"<body>"
                           b"<span>Hello, world!</span>"
                           b"</body>"
                           b"</html>")
        client.close()


def main():
    main_server()

if __name__ == "__main__":
    main()
