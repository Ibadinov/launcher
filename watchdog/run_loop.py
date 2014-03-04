# -*- coding: utf-8 -*-
"""
    watchdog
    ~~~~~~~~

    :copyright: (c) 2014 by Marat Ibadinov.
    :license: MIT, see LICENSE for more details.
"""

from Queue import Queue, Empty


class RunLoop(object):
    def __init__(self):
        self.queue = Queue()

    def run(self):
        while True:
            try:
                self.queue.get_nowait()()
            except Empty:
                break

    def run_once(self):
        try:
            self.queue.get_nowait()()
        except Empty:
            pass

    def postpone(self, callable):
        self.queue.put(callable)
