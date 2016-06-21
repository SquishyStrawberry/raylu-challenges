#!/usr/bin/env python3
import os


def foo():
    with open(os.path.join("tmp", "hello_world.txt"), "w") as fobj:
        fobj.write(str(os.getpid()))

def bar():
    with open(os.path.join("tmp", "hello_world.txt"), "w") as fobj:
        fobj.write(str(os.getpid() * 2))
