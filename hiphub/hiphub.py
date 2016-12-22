#!/usr/bin/python3
# -*- python-indent-offset: 4 -*-

import sys
import pwd
import time
import daemon
import lockfile

from pathlib import Path

daemon_username = "hiphub"
update_dir = Path('/var/www/hip.zijistark.com/hiphub')
root_repo_dir = Path('/var/local/git')
pidfile_path = Path('/home') / daemon_username / 'hiphub.pid'

repos = {
    'SWMH-BETA': ['master', 'Timeline_Extension+Bookmark_BETA'],
    'sed2': ['dev', 'timeline'],
    'EMF': ['alpha', 'timeline'],
    'MiniSWMH': ['master', 'timeline'],
    'HIP-tools': ['master'],
    'ck2utils': ['dev'],
    'CPRplus': ['dev'],
    'ARKOpack': ['master'],
    'ArumbaKS': ['master'],
    'LTM': ['master', 'dev']
}


def fatal(msg):
    sys.stderr.write('fatal: ' + msg + '\n')
    sys.stderr.flush()
    sys.exit(1)


def main():
    context = daemon.DaemonContext()
    context.working_directory = str(update_dir)

    # we'll be running as the `daemon_username` under its default group
    pwent = pwd.getpwnam(daemon_username)
    context.uid = pwent[2]
    context.gid = pwent[3]

    # this is a bit messy (really shouldn't have to check for the '.lock' file ourselves)
    pidfile_lock = lockfile.FileLock(str(pidfile_path))

    if Path(pidfile_lock.path + '.lock').exists():
        fatal('hiphub appears to already be running')
    
    context.pidfile = pidfile_lock

    # for debugging purposes, we may want to NOT detach our
    # stdout/stderr, so use -F for foreground mode (even though it's
    # not really in the foreground-- still a daemon)
    if '-F' in sys.argv[1:]:
        context.stdout = sys.stdout
        context.stderr = sys.stderr
    
    with context:
        while True:
            time.sleep(1)


if __name__ == '__main__':
    main()
