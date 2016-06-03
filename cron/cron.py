#!/usr/bin/env python3.5
import heapq
import threading
import time

tasks = []
new_tasks = threading.Condition()
no_tasks = threading.Event()


def init():
    threading.Thread(target=task_runner, daemon=True).start()


def schedule(seconds, function):
    with new_tasks:
        heapq.heappush(tasks, (time.time() + seconds, function))
        no_tasks.clear()
        new_tasks.notify()


def wait():
    no_tasks.wait()


def task_runner():
    while True:
        new_tasks.acquire()
        if not tasks:
            no_tasks.set()
            new_tasks.wait()
        when, what = tasks[0]
        now = time.time()
        if when < now:
            heapq.heappop(tasks)
            new_tasks.release()
            threading.Thread(target=what).start()
        else:
            new_tasks.wait(when - now)
            new_tasks.release()
