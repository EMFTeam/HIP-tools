#!/usr/bin/python3
# -*- python-indent-offset: 4 -*-

VERSION='0.01'

import os
import sys
import pwd
import time
import signal
import logging
import subprocess
import daemon
import lockfile
from pathlib import Path

g_daemon_user = 'hiphub'  # user hiphub should run as (will use user's default group)
g_base_dir = Path('/home') / g_daemon_user  # daemon state will be kept under here
g_webhook_dir = Path('/var/www/hip.zijistark.com/hiphub')  # folder where the webhook hints us as to new commit activity
g_root_repo_dir = Path('/var/local/git')  # root folder of all the hiphub git repositories
g_gitbin_path = Path('/usr/bin/git')

# repos and respective branches which we track
g_repos = {
    'SWMH-BETA': ['master', 'Timeline_Extension+Bookmark_BETA'],
    'sed2': ['dev', 'timeline'],
    'EMF': ['alpha', 'timeline'],
    'MiniSWMH': ['master', 'timeline'],
    'HIP-tools': ['master'],
    'ck2utils': ['dev'],
    'CPRplus': ['dev'],
    'ARKOpack': ['master'],
    'ArumbaKS': ['master'],
    'LTM': ['master', 'dev'],
}

g_pidfile_path = g_base_dir / 'hiphub.pid'  # we mark our currently running PID here
g_state_dir = g_base_dir / 'state'  # we store the last-processed SHA for each tracked head within files in this folder
g_logfile_path = g_base_dir / 'hiphub.log'  # we log info and errors here (once the daemon is off the ground and no longer attached to a session/terminal)


def fatal(msg):
    sys.stderr.write('fatal: ' + msg + '\n')
    sys.stderr.flush()
    sys.exit(1)


def shutdown_daemon():
    g_pidfile_path.unlink()
    logging.info('hiphub v{} shutting down with pid {}...'.format(VERSION, os.getpid()))
    sys.exit(0)

    
class TooManyRetriesException(Exception):
    def __str__(self):
        return 'Retried command too many times'


def git_run(args, retry=False):
    cmd = [str(g_gitbin_path)] + args
    n_tries = 0
    
    while True:
        cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        n_tries += 1

        if cp.returncode == 0:
            return cp
        else:
            logging.error('git failed:\n>command: {}\n>code: {}\n>stdout:\n{}\n>stderr:\n{}\n'
                          .format(cp.args, cp.returncode, cp.stdout, cp.stderr))

            if not retry:
                cp.check_returncode()  # will throw for us
            elif n_tries == 1000:
                raise TooManyRetriesException()
            
            # TODO: finish this once we know a) what git will typically give us on stderr vs. stdout,
            # and b) what the errors for transient network issues tend to look like, as we only want to
            # to do "infinite" retry for those. [until then, setup errors and the like are just going to
            # keep printing a lot of failures to the log for a very long time if retries were enabled.]
            time.sleep(60)


def update_head(repo, branch):
    os.chdir(str(g_root_repo_dir / repo))
    git_run(['reset', '--hard', 'HEAD'])
    git_run(['checkout', branch])
    git_run(['reset', '--hard', 'HEAD'])
    git_run(['pull'])
    cp = git_run(['rev-parse', 'HEAD'])
    os.chdir(str(g_base_dir))
    return cp.stdout.strip()

    
def update_all_heads():
    logging.debug('updating all tracked heads...')
    
    for repo in g_repos:
        logging.debug('refreshing repository {}...'.format(repo))
        for branch in g_repos[repo]:
            update_head(repo, branch)
    

def init_daemon():
    # mark our tracks with pidfile
    with g_pidfile_path.open("w") as f:
        f.write('{}\n'.format(os.getpid()))

    # created needed directories on-demand
    if not g_state_dir.exists():
        logging.debug('state folder does not exist, creating: {}'.format(g_state_dir))
        g_state_dir.mkdir(parents=True)

    update_all_heads()


def main():
    context = daemon.DaemonContext()
    context.working_directory = str(g_base_dir)

    # we'll be running as the `daemon_username` under its default group
    pwent = pwd.getpwnam(g_daemon_user)
    context.uid = pwent[2]
    context.gid = pwent[3]

    if g_pidfile_path.exists():
        fatal('hiphub appears to already be running or to have terminated ungracefully')

    context.pidfile = lockfile.FileLock(str(g_pidfile_path))

    context.signal_map = {
        signal.SIGTERM: shutdown_daemon,
        signal.SIGHUP: shutdown_daemon,
        }

    context.umask = 0o002
    
    # for debugging purposes, we may want to NOT detach our
    # stdout/stderr, so use -F for foreground mode (even though it's
    # not really in the foreground-- still a daemon)
    if '-F' in sys.argv[1:]:
        context.stdout = sys.stdout
        context.stderr = sys.stderr
    
    with context:
        # initialize logging
        logging.basicConfig(filename=str(g_logfile_path),
                            format='%(asctime)s> %(levelname)s: %(message)s',
                            datefmt='%Y/%m/%d %H:%M:%S',
                            level=logging.DEBUG)

        # and on with the show!
        try:
            logging.info('hiphub v{} starting with pid {}...'.format(VERSION, os.getpid()))
            init_daemon()
        except Exception as e:
            # will direct a traceback to the log
            logging.exception("unhandled exception, hiphub must terminate:")
            sys.exit(255)


if __name__ == '__main__':
    main()
