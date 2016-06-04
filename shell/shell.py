#!/usr/bin/env python3
import os
import signal


def main():
    while True:
        try:
            command, *args = input("> ").split()
        except ValueError:
            continue
        except EOFError:
            break
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
                if len(args) >= 2 and args[-2] == ">":
                    if not os.path.exists(args[-1]):
                        os.mknod(args[-1])
                    os.dup2(os.open(args[-1], os.O_WRONLY), 1)
                    args = args[:-2]
                os.execvp(command, [command, *args])
                raise RuntimeError("This should never happen!")
            else:
                signal.signal(signal.SIGINT,
                              lambda *_: os.kill(pid, signal.SIGINT))
                os.waitpid(pid, 0)
                signal.signal(signal.SIGINT, signal.SIG_DFL)

if __name__ == "__main__":
    main()
