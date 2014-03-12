# -*- coding: utf-8 -*-
"""
    launcher
    ~~~~~~~~

    :copyright: (c) 2014 by Marat Ibadinov.
    :license: MIT, see LICENSE for more details.
"""

from .run_loop import RunLoop
from .schedule import previous as schedule_previous
from .schedule import next as schedule_next
from collections import OrderedDict

import logging
import os
import signal
import sys
import time


def shell_execv(filename, argv):
    with open(filename) as file:
        if file.read(2) == '#!':
            args = file.readline().strip().split(' ')
            # change STDIN to that file
            os.dup2(os.open(filename, os.O_RDONLY), sys.stdin.fileno())
            trampoline = '/usr/bin/env'
            # argv[0] for trampoline is trampoline's path
            # append filename since we should pass script name to interpreter
            os.execv(trampoline, [trampoline] + args + [filename] + argv)

    os.execv(filename, [filename] + argv)


class Launcher(object):
    def __init__(self, load_launch_time=None, store_launch_time=None, on_exit=None):
        self.store = {}
        self.load_launch_time = load_launch_time or (lambda id: self.store.get(id) or 0)
        self.store_launch_time = store_launch_time or (lambda id, ts: self.store.update({id: ts}))
        self.on_exit = on_exit or (lambda id, status, is_normal: None)
        self.commands = {}
        self.processes = {}
        self.pending = OrderedDict()
        self.run_loop = RunLoop()
        signal.signal(signal.SIGCHLD, self._handle_sigchld)

    def run(self, timeout=None):
        timeout = timeout or 60
        self.run_loop.run()
        if self.pending:
            first = self.pending.items()[0][1]
            delay = max(0, min(timeout, first - time.time()))
        else:
            delay = timeout
        time.sleep(delay)
        self._launch_pending()

    def terminate(self):
        self._terminate_processes(self.processes)

    def set_commands(self, commands):
        for id, command in commands.items():
            if id not in self.commands:
                self._postpone(id, command)
            elif command != self.commands[id]:
                self._terminate_process(id)
                self._postpone(id, command)
        for id, command in self.commands.items():
            if id not in commands:
                self._terminate_process(id)
        self.commands = dict(commands)

    def _handle_sigchld(self, signo, frame):
        while True:
            try:
                # raises OSError with ECHILD code when there is no child processes
                # returns pid=0 when there is no exited child
                pid, status, rusage = os.wait3(os.WNOHANG)
                if not pid:
                    break
            except OSError:
                break
            self.run_loop.postpone(lambda p=pid, s=status, r=rusage: self._child_exited(p, s, r))

    def _child_exited(self, pid, status, rusage):
        id = self.processes.pop(pid)
        self._log_exit(id, pid, status)
        self.on_exit(id, status, self._is_normal_exit(status))

        if id not in self.commands:
            return  # command was removed from data source
        command = self.commands[id]
        if not self._is_normal_exit(status) and command.get('respawn'):
            self._postpone(id, command)
        elif command.get('schedule') or command.get('interval'):
            self._postpone(id, command)

    def _postpone(self, id, command):
        previous = self.load_launch_time(id)
        timestamp = self._get_launch_time(command, previous)
        self.pending[id] = timestamp
        self.pending = OrderedDict(sorted(self.pending.items(), key=lambda item: item[1]))
        formatted_time = time.strftime('%H:%M %b %d', time.gmtime(timestamp))
        logging.info("Will launch %s at %s", id, formatted_time)

    def _launch_pending(self):
        while self.pending:
            id, timestamp = self.pending.items()[0]
            if timestamp > time.time():
                break
            self.pending.pop(id)
            self._launch_process(id)

    def _launch_process(self, id):
        command = self.commands[id]['command']
        pid = self._execute_command(command)
        self.processes[pid] = id
        logging.info("Launched %s[%s]: %s", id, pid, command)
        self.store_launch_time(id, time.time())

    def _execute_command(self, command):
        pid = os.fork()
        if pid == 0:
            # child process
            # create new process group with identifier equal to current process id
            # and become a session leader
            # group will be used to terminate child process along with it's children
            os.setsid()
            # exec command in current process scope
            command = command.split(' ')
            shell_execv(command[0], command[1:])
        # parent process
        return pid

    def _terminate_processes(self, processes):
        for pid, id in processes.items():
            logging.info("Terminating %s[%s]", id, pid)
            os.kill(-pid, signal.SIGTERM)

    def _terminate_process(self, id):
        processes = {pid: name for pid, name in self.processes.items() if id == name}
        self._terminate_processes(processes)

    def _get_launch_time(self, command, previous):
        schedule = command.get('schedule')
        interval = command.get('interval')
        if schedule:
            now = time.time()
            if previous < schedule_previous(schedule, now):
                return now
            return schedule_next(schedule, now)
        if interval:
            return max(previous + interval, time.time())
        return time.time()

    def _is_normal_exit(self, status):
        if os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0:
            return True
        if os.WIFSIGNALED(status) and os.WTERMSIG(status) == signal.SIGTERM:
            return True
        return False

    def _log_exit(self, id, pid, status):
        if os.WIFEXITED(status):
            logging.info("Child %s[%d] exited with status %d", id, pid, os.WEXITSTATUS(status))
        elif os.WIFSIGNALED(status):
            signo = os.WTERMSIG(status)
            logging.info("Child %s[%d] exited due to uncaught signal %d", id, pid, signo)
        else:
            logging.info("Child %s[%d] exited, but causes are unknown", id, pid)
