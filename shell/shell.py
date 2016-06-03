#!/usr/bin/env python3
import os


def main():
    while True:
        command, *args = input("> ").split()
        if command == "cd":
            if len(args) < 2:
                os.chdir(os.environ["HOME"])
            else:
                os.chdir(args[1])
        elif command == "pwd":
            print(os.getcwd())
        else:
            pid = os.fork()
            if pid == 0:
                if len(args) >= 3 and args[-2] == ">":
                    if not os.path.exists(args[-1]):
                        with open(args[-1], "w") as _:
                            pass
                    os.dup2(os.open(args[-1], os.O_WRONLY), 1)
                    args = args[:-2]
                os.execvp(command, [command, *args])
                raise RuntimeError("This should never happen!")
            else:
                os.waitpid(pid, 0)

if __name__ == "__main__":
    main()
