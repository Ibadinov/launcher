# -*- coding: utf-8 -*-
"""
    watchdog
    ~~~~~~~~

    :copyright: (c) 2014 by Marat Ibadinov.
    :license: MIT, see LICENSE for more details.
"""

from .schedule import previous as schedule_previous
from .schedule import next as schedule_next
from collections import OrderedDict

import logging
import signal
import time
import os


def shell_execv(filename, argv):
    with open(filename) as file:
        if file.read(2) == '#!':
            args = file.readline().strip().split(' ')
            # change STDIN to that file
            os.dup2(os.open(filename, os.O_RDONLY), stdin.fileno())
            trampoline = '/usr/bin/env'
            # argv[0] for trampoline is trampoline's path
            # append filename since we should pass script name to interpreter
            execv(trampoline, [trampoline] + args + [filename] + argv)

    execv(filename, [filename] + argv[2:])


class Watchdog(object):
    def __init__(self, load_launch_time=None, store_launch_time=None, on_exit=None):
        self.load_launch_time = load_launch_time or (lambda id: 0)
        self.store_launch_time = store_launch_time or (lambda id, timestamp: None)
        self.on_exit = on_exit or (lambda id, status, is_normal: None)
        self.commands = {}
        self.processes = {}
        self.pending = OrderedDict()
        signal.signal(signal.SIGCHLD, self._handle_sigchld)

    def run(self, timeout=None):
        timeout = timeout or 60
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
        for id, command in commands:
            if id not in self.commands:
                self._postpone(id, command)
            elif command != self.commands[id]:
                self._terminate_process(id)
                self._postpone(id, command)
        for id, command in self.commands:
            if id not in commands:
                self._terminate_process(id)
        self.commands = dict(commands)

    def _handle_sigchld(self, signo):
        while True:
            pid, status, rusage = os.wait3(os.WNOHANG)
            if not pid:
                break
            self._child_exited(pid, status, rusage)

    def _child_exited(self, pid, status, rusage):
        id = self.processes.pop(pid)
        self._log_exit(id, pid, status)
        self.on_exit(id, status, self._is_normal_exit(status))

        command = self.commands[id]
        if not self._is_normal_exit(status) and command.get('respawn'):
            self._postpone(id, command)
        elif command.get('schedule') or command.get('interval'):
            self._postpone(id, command)

    def _postpone(self, id, command):
        previous = self.load_launch_time(id)
        self.pending[id] = self._get_launch_time(command, previous)
        self.pending = OrderedDict(sorted(self.pending.items(), key=lambda item: item[1]))
        logging.info("Will launch %s at %s", id, time.strftime('H:M m d', time.gmtime(timestamp)))

    def _launch_pending(self):
        while self.pending:
            id, timestamp = self.pending.items()[0]
            if timestamp > time.time():
                break
            self._launch_process(id)
            self.pending.pop(id)

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
        for pid, id in processes:
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

    def _log_exit(self, pid, status):
        if os.WIFEXITED(status):
            logging.info("Child %s[%d] exited with status %d", id, pid, os.WEXITSTATUS(status))
        elif os.WIFSIGNALED(status):
            signo = os.WTERMSIG(status)
            logging.info("Child %s[%d] exited due to uncaught signal %d", id, pid, signo)
        else:
            logging.info("Child %s[%d] exited, but causes are unknown", id, pid)
