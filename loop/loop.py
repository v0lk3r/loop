#!/usr/bin/env python
#! -*- coding: utf-8 -*-

import subprocess
import os
import sys
import logging
import time
import fnmatch

from inotify import watcher
import inotify

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s:%(name)s: %(message)s',
                    datefmt='%H:%M:%S'
                )
log = logging.getLogger('loop')


class Loop(object):
    default_ignore_pattern = ['*/.#*',  # emacs tmp files,
                              '*/.git*',  # git tmp files
    ]

    def __init__(self, cmd, path):
        self.cmd = cmd
        self.path = path
        self.active_process = None
        self.file_ignore_pattern = self.init_file_filter()
        self.watcher = self.init_watcher()
        self.dispatch_cmd()
        self.watch_loop()

    def init_file_filter(self):
        file_ignore_pattern = []
        file_ignore_pattern.extend(self._add_git_ignored())
        file_ignore_pattern.extend(self.default_ignore_pattern)
        return file_ignore_pattern

    def _add_git_ignored(self):
        def get_git_ignore_path():
            path = self.path
            while path != '/':
                gi = os.path.join(path, '.gitignore')
                if os.path.exists(gi):
                    return os.path.realpath(gi)
                path = os.path.join(path, os.pardir)
            return None
        git_ignore_path = get_git_ignore_path()
        if git_ignore_path:
            with open(git_ignore_path) as f:
                return [os.path.join(os.path.dirname(git_ignore_path), line.strip())
                        for line in f.read().split('\n') if line]
        else:
            return []

    def is_watched(self, fn):
        if any(fnmatch.fnmatch(fn, ignored_path)
               for ignored_path in self.file_ignore_pattern):
            return False
        log.info('watched file changed/created: {}'.format(fn))
        return True

    def init_watcher(self):
        w = watcher.AutoWatcher()
        w.add_all(self.path, inotify.IN_MODIFY | inotify.IN_CREATE)
        if not w.num_watches():
            log.error('no files to watch')
            sys.exit(1)
        return w

    def dispatch_cmd(self):
        time.sleep(0.01)
        if self.active_process:
            self.check_process()
            log.info('process killed')
            self.active_process.kill()
        cmd_str = ' '.join(self.cmd)
        try:
            self.active_process = subprocess.Popen(self.cmd)
        except OSError as e:
            log.error('ERROR with command: {0} MESSAGE: {1}'.format(cmd_str, e.strerror))
            sys.exit(1)
        log.info('cmd dispatched: {}'.format(cmd_str))

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
                try:
                    subprocess.call(notify)
                except OSError as e:
                    log.warn('notification not send. error: {}'.format(e.strerror))

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


def main():
    path = os.path.abspath(os.path.curdir)
    cmd = sys.argv[1:]
    Loop(cmd, path)

if __name__ == '__main__':
    main()
