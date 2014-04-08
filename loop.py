#!/usr/bin/env python
#! -*- coding: utf-8 -*-

import subprocess
import os
import sys
import logging
import time

from inotify import watcher
import inotify
import git

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)-15s:%(name)s: %(message)s')
log = logging.getLogger('watcher')


class Loop(object):

    def __init__(self, cmd, path):
        self.cmd = cmd
        self.path = path
        self.active_process = None
        self.init_file_filter()
        self.watcher = self.init_watcher()
        self.dispatch_cmd()
        self.watch_loop()

    def init_file_filter(self):
        g = git.Git(self.path)
        try:
            self.known_files = [os.path.abspath(fn) for fn in g.ls_files().split('\n')]
        except git.GitCommandError:
            self.known_files = []

    def is_watched(self, fn):
        if self.known_files and fn not in self.known_files:
            return False
        return True

    def init_watcher(self):
        w = watcher.AutoWatcher()
        w.add_all(self.path, inotify.IN_MODIFY | inotify.IN_CREATE)
        if not w.num_watches():
            print 'no files to watch'
            sys.exit(1)
        return w

    def dispatch_cmd(self):
        time.sleep(0.01)
        if self.active_process:
            self.check_process()
            log.info('process killed')
            self.active_process.kill()
        self.active_process = subprocess.Popen(self.cmd)
        log.info('cmd dispatched: {}'.format(self.cmd))

    def check_process(self):
        if self.active_process:
            ret = self.active_process.poll()
            if ret is not None:
                self.active_process = None
                log.info('process returned with {}'.format(ret))
                status = 'SUCCESS!' if ret <= 0 else 'FAIL'
                notify = ['notify-send', '{0}'.format(status), ' '.join(self.cmd)]
                if status == 'FAIL':
                    notify[1:1] = ['-u', 'critical']
                subprocess.call(notify)

    def watch_loop(self):
        try:
            while self.watcher.num_watches():
                dispatch = False
                if any(self.is_watched(event.fullpath)
                       for event in self.watcher.read(0)):
                    dispatch = True
                if dispatch:
                    self.dispatch_cmd()
                else:
                    self.check_process()
                time.sleep(0.05)
        except KeyboardInterrupt:
            if self.active_process:
                self.active_process.kill()
                log.info('running process killed')


def start_watcher():
    path = os.path.abspath(os.path.curdir)
    cmd = sys.argv[1:]
    Loop(cmd, path)

if __name__ == '__main__':
    start_watcher()
