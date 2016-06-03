#!/usr/bin/env python3
import os


def main():
    while True:
        command, *args = input("> ").split()
        pid = os.fork()
        if pid == 0:
            os.execvp(command, [command, *args])
        os.wait()

if __name__ == "__main__":
    main()
