#!/usr/bin/env python3
import os


def main():
    while True:
        command, *args = input("> ").split()
        os.execvp(command, [command, *args])

if __name__ == "__main__":
    main()
