#!/usr/bin/env python3
import os


def main():
    while True:
        command, *args = input("> ").split()
        pid = os.fork()
        if pid == 0:
            if len(args) >= 3 and args[-2] == ">":
                if not os.path.exists(args[-1]):
                    with open(args[-1], "w") as f:
                        pass
                os.dup2(os.open(args[-1], os.O_WRONLY), 1)
                args = args[:-2]
            os.execvp(command, [command, *args])
        os.wait()

if __name__ == "__main__":
    main()
