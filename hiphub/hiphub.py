#!/usr/bin/python3
# -*- python-indent-offset: 4 -*-

VERSION='0.06'

import os
import re
import sys
import pwd
import time
import signal
import daemon
import logging
import lockfile
import subprocess
from pathlib import Path

##########

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

##########


class TooManyRetriesException(Exception):
    def __str__(self):
        return 'Retried command too many times'

    
class RebuildFailedException(Exception):
    def __str__(self):
        return 'Rebuild of downstream repository failed'


def fatal(msg):
    sys.stderr.write('fatal: ' + msg + '\n')
    sys.stderr.flush()
    sys.exit(1)


def git_run(args, retry=False):
    cmd = [str(g_gitbin_path)] + args
    n_tries = 0

    while True:
        cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        n_tries += 1

        if cp.returncode == 0:
            return cp
        else:
            logging.error('git failed:\n>command: {}\n>code: {}\n>error:\n{}\n'.format(cp.args, cp.returncode, cp.stderr))

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
    logging.debug('updating head: %s/%s', repo, branch)
    os.chdir(str(g_root_repo_dir / repo))

    # first, make the repo a carbon copy of HEAD -- remove changes to index, remove untracked changes
    git_run(['reset', '--hard', 'HEAD'])
    git_run(['clean', '-f'])

    # now checkout the desired branch and pull
    git_run(['checkout', branch])
    git_run(['pull'], retry=True)

    # determine the head's possibly-new SHA
    cp = git_run(['rev-parse', 'HEAD'])

    os.chdir(str(g_base_dir))
    return cp.stdout.strip()


def git_files_changed(repo, branch, old_rev, new_rev='HEAD'):
    os.chdir(str(g_root_repo_dir / repo))
    git_run(['checkout', branch])
    cp = git_run(['log', '--pretty=format:', '-z', '--name-only', '{}..{}'.format(old_rev, new_rev)])
    changed_files = { Path(path) for path in cp.stdout.split('\x00') if path }

    os.chdir(str(g_base_dir))
    return changed_files


def has_this_repo_changed(ignored_file=None):
    cp = git_run(['status', '-z'])  # filenames are terminated with NUL instead of line break
    status_iter = iter(cp.stdout.split('\x00')[:-1])  ## example entry: '?? i got mad spaces and am untracked, yo.txt'
    for entry in status_iter:
        if entry[0] == 'R':
            next(status_iter)  # there is an extra filename (what path was renamed from). skip it
        path = entry[3:]
        if ignored_file is None or path != ignored_file:
            return True
    return False


def load_state():
    global g_ignored_rev
    g_ignored_rev = {}
    global g_last_rev
    g_last_rev = {}
    for r in g_repos:
        for b in g_repos[r]:
            h = '{}:{}'.format(r, b)
            g_ignored_rev[h] = None
            p = g_state_dir / h
            if p.exists():
                with p.open() as f:
                    g_last_rev[h] = f.read().strip()


# assuming repo is SWMH-BETA and we've processed SWMH-BETA before
# (s.t. we have a list of files changed), should we rebuild MiniSWMH?
def should_rebuild_mini(repo, branch, changed_files):
    assert repo == 'SWMH-BETA', 'should_rebuild_mini: unsupported trigger repository: ' + repo
    specific_paths = ['SWMH/common/landed_titles/swmh_landed_titles.txt',
                      'SWMH/common/province_setup/00_province_setup.txt',
                      'SWMH/map/default.map',
                      'SWMH/map/definition.csv']

    if any(Path(p) in changed_files for p in specific_paths):
        return True
    p_wanted_file = r'^SWMH/history/(?:titles|provinces)/.+?\.txt$'
    return any(re.match(p_wanted_file, str(f)) for f in changed_files)


def should_rebuild_sed(repo, branch, changed_files):
    assert repo == 'MiniSWMH' or repo == 'SWMH-BETA', 'should_rebuild_sed: unsupported trigger repository: ' + repo
    prefix = repo if repo == 'MiniSWMH' else 'SWMH'
    landed_titles = Path(prefix) / Path('common/landed_titles')
    if any(landed_titles in p.parents for p in changed_files):
        return True
    i18n = Path(prefix) / Path('localisation')
    return any(i18n in p.parents for p in changed_files)


def rebuild_mini(swmh_branch):
    logging.info('rebuilding MiniSWMH...')
    # get on the right branches
    mini_branch = g_repos['MiniSWMH'][g_repos['SWMH-BETA'].index(swmh_branch)]
    os.chdir(str(g_root_repo_dir / 'SWMH-BETA'))
    git_run(['checkout', swmh_branch])
    os.chdir(str(g_root_repo_dir / 'ck2utils'))
    git_run(['checkout', 'dev'])
    os.chdir(str(g_root_repo_dir / 'MiniSWMH'))
    git_run(['checkout', mini_branch])

    cp = subprocess.run(['/usr/bin/python3', 'build_mini.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    if cp.returncode != 0:
        logging.error('failed to rebuild MiniSWMH:\n>command: {}\n>code: {}\n>error:\n{}\n'.format(cp.args, cp.returncode, cp.stderr))
        git_run(['reset', '--hard', 'HEAD'])
        git_run(['clean', '-f'])
        os.chdir(str(g_base_dir))
        raise RebuildFailedException()

    # did anything change besides our version.txt?
    version_file = 'MiniSWMH/version.txt'
    if not has_this_repo_changed(ignored_file=version_file):
        # eh, no biggie-- cleanup version.txt and go
        git_run(['checkout', version_file])
        os.chdir(str(g_base_dir))
        return None

    # if we're here, we do indeed have changes to commit.
    git_run(['add', '-A'])
    git_run(['commit', '-a', '-m', 'rebuild from upstream changes :robot_face:'])

    # determine the head's new SHA so that we may ignore it for future processing
    new_rev = git_run(['rev-parse', 'HEAD']).stdout.strip()
    g_ignored_rev['MiniSWMH:' + mini_branch] = new_rev

    # .. and puuuuush, deep breaths
    git_run(['push'], retry=True)

    # ta-dah!
    logging.info('rebuild of MiniSWMH resulted in net change. pushed new MiniSWMH (%s)', new_rev)
    os.chdir(str(g_base_dir))
    return new_rev


def rebuild_sed(repo, branch):
    logging.info('rebuilding sed2...')

    # get on the right branches
    sed_branch = g_repos['sed2'][g_repos[repo].index(branch)]
    emf_branch = g_repos['EMF'][g_repos[repo].index(branch)]
    mini_branch = g_repos['MiniSWMH'][g_repos[repo].index(branch)]
    swmh_branch = g_repos['SWMH-BETA'][g_repos[repo].index(branch)]
    os.chdir(str(g_root_repo_dir / 'SWMH-BETA'))
    git_run(['checkout', swmh_branch])
    os.chdir(str(g_root_repo_dir / 'MiniSWMH'))
    git_run(['checkout', mini_branch])
    os.chdir(str(g_root_repo_dir / 'EMF'))
    git_run(['checkout', emf_branch])
    os.chdir(str(g_root_repo_dir / 'sed2'))
    git_run(['checkout', sed_branch])

    cp = subprocess.run(['/usr/bin/python3', 'build.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    if cp.returncode != 0:
        logging.error('failed to rebuild sed2:\n>command: {}\n>code: {}\n>error:\n{}\n'.format(cp.args, cp.returncode, cp.stderr))
        git_run(['reset', '--hard', 'HEAD'])
        git_run(['clean', '-f'])
        os.chdir(str(g_base_dir))
        raise RebuildFailedException()

    # did anything change besides our version.txt?
    version_file = 'build/SED2/version.txt'
    if not has_this_repo_changed(ignored_file=version_file):
        # eh, no biggie-- cleanup version.txt and go
        git_run(['checkout', version_file])
        os.chdir(str(g_base_dir))
        return None

    # if we're here, we do indeed have changes to commit.
    git_run(['add', '-A'])
    git_run(['commit', '-a', '-m', 'rebuild from upstream changes :robot_face:'])

    # determine the head's new SHA so that we may ignore it for future processing
    new_rev = git_run(['rev-parse', 'HEAD']).stdout.strip()
    g_ignored_rev['sed2:' + sed_branch] = new_rev

    # .. and puuuuush, deep breaths
    git_run(['push'], retry=True)

    # ta-dah!
    logging.info('rebuild of sed2 resulted in net change. pushed new sed2 (%s).', new_rev)
    os.chdir(str(g_base_dir))
    return new_rev


def process_head_change(repo, branch, head_rev):
    head = '{}:{}'.format(repo, branch)
    do_processing = True
    processing_failed = False
    
    logging.debug('processing head change: %s/%s to rev %s', repo, branch, head_rev)
    
    if g_ignored_rev[head] is head_rev:
        logging.debug('skipped processing for rev due to being self-emitted')
        do_processing = False

    g_ignored_rev[head] = None

    if do_processing:
        build_mini = False
        build_sed = False

        if repo == 'SWMH-BETA':
            if head in g_last_rev:
                changed_files = git_files_changed(repo, branch, g_last_rev[head])
                build_mini = should_rebuild_mini(repo, branch, changed_files)
                build_sed = build_mini or should_rebuild_sed(repo, branch, changed_files)
            else:  # first time (all files in repo changed, effectively)
                build_mini = True
                build_sed = True
        elif repo == 'MiniSWMH':
            if head in g_last_rev:
                changed_files = git_files_changed(repo, branch, g_last_rev[head])
                build_sed = should_rebuild_sed(repo, branch, changed_files)
            else:
                build_sed = True

        try:
            if build_mini:
                rebuild_mini(branch)
            if build_sed:
                rebuild_sed(repo, branch)
        except RebuildFailedException:
            processing_failed = True

    if not processing_failed:  # don't advance last-processed rev for this head unless its processing tasks completed OK
        # update memory state
        g_last_rev[head] = head_rev

        # update state on disk
        with (g_state_dir / head).open('w') as f:
            print(head_rev, file=f)


def init_daemon():
    # mark our tracks with pidfile
    with g_pidfile_path.open('w') as f:
        print(os.getpid(), file=f)

    # deprioritize our process scheduling priority (as well as our subprocesses')
    os.nice(10)

    # created needed directories on-demand
    if not g_state_dir.exists():
        logging.debug('state folder does not exist, creating: {}'.format(g_state_dir))
        g_state_dir.mkdir(parents=True)

    # reset our environment to something appropriate for the `g_daemon_user`
    env_vars_to_del = ['LOGNAME', 'LS_COLORS', 'SUDO_GID', 'SUDO_UID', 'SUDO_USER', 'SUDO_COMMAND',
                       'TERM', 'MAIL', 'USER', 'HOME', 'USERNAME']

    for v in env_vars_to_del:
        if v in os.environ:
            del os.environ[v]

    os.environ['LOGNAME'] = g_daemon_user
    os.environ['USER'] = g_daemon_user
    os.environ['USERNAME'] = g_daemon_user
    os.environ['TERM'] = 'xterm'
    os.environ['HOME'] = '/home/' + g_daemon_user
    
    # some of our python child processes will need this for localpaths.py and such
    os.environ['PYTHONPATH'] = str(g_root_repo_dir / 'ck2utils/esc')

    env_dump = 'daemon environment (after adjustment):\n'
    for k in os.environ:
        env_dump += k + '=' + os.environ[k] + '\n'

    logging.debug(env_dump)
    
    load_state()

    logging.debug('updating all tracked heads...')
    proc_needed = []

    for repo in g_repos:
        for branch in g_repos[repo]:
            rev = update_head(repo, branch)
            h = '{}:{}'.format(repo, branch)
            if rev != g_last_rev.get(h):
                proc_needed.append( (repo, branch, rev) )

    # TODO: might want to sort proc_needed so that, e.g., SWMH-BETA < MiniSWMH < EMF

    for pn in proc_needed:
        process_head_change(*pn)


def run_daemon():
    last_mtime = {}

    # initialize file mtimes
    for r in g_repos:
        for b in g_repos[r]:
            h = '{}:{}'.format(r, b)
            p = g_webhook_dir / h
            if p.exists():
                last_mtime[h] = p.stat().st_mtime

    while True:
        time.sleep(1)  # one-second polling interval

        changed_heads = []
        for r in g_repos:
            for b in g_repos[r]:
                h = '{}:{}'.format(r, b)
                p = g_webhook_dir / h
                if p.exists() and (h not in last_mtime or p.stat().st_mtime > last_mtime[h]):
                    logging.debug('webhook received push event: %s/%s', r, b)
                    changed_heads.append( (r, b) )
                    last_mtime[h] = p.stat().st_mtime

        proc_needed = []
        for c in changed_heads:
            rev = update_head(*c)
            proc_needed.append( (*c, rev) )

        # TODO: might want to sort proc_needed so that, e.g., SWMH-BETA < MiniSWMH < EMF

        for pn in proc_needed:
            process_head_change(*pn)


def shutdown_daemon(exit_code=0):
    try:
        logging.info('hiphub v{} shutting down with pid {}...'.format(VERSION, os.getpid()))
    except Exception as e:
        pass

    g_pidfile_path.unlink()
    sys.exit(exit_code)


# NOTE: this *_daemon function is not called from within a daemon context
def kill_existing_daemon():
    if not g_pidfile_path.exists():
        return

    # get the PID of the running hiphub daemon
    with g_pidfile_path.open() as f:
        pid = int(f.read().strip())

    print('sending SIGTERM to running daemon with pid {}...'.format(pid))
    os.kill(pid, signal.SIGTERM)  # send it a SIGTERM so that it may gracefully shutdown

    # now block until the pidfile is removed (100ms poll interval, up
    # to 300 polls allowed for approx. 30sec of allowed wait before
    # timing out).

    n_tries = 0
    need_hard_kill = False

    while True:
        time.sleep(0.1)
        n_tries += 1
        if not g_pidfile_path.exists():
            break
        elif n_tries == 300:
            need_hard_kill = True
            break

    if need_hard_kill:
        print('warning: since running daemon did not respond to SIGTERM, sending SIGKILL...')
        os.kill(pid, signal.SIGKILL)
        if g_pidfile_path.exists():
            g_pidfile_path.unlink()


def sig_terminate_handler(sig_num, stack_frame):
    shutdown_daemon()


def main():
    opt_restart = '--restart' in sys.argv[1:]

    context = daemon.DaemonContext()
    context.working_directory = str(g_base_dir)

    # we'll be running as the `daemon_username` under its default group
    pwent = pwd.getpwnam(g_daemon_user)
    context.uid = pwent[2]
    context.gid = pwent[3]

    if g_pidfile_path.exists():
        if opt_restart:
            kill_existing_daemon()
        else:
            fatal('hiphub appears to already be running (use --restart to force a restart)')

    context.pidfile = lockfile.FileLock(str(g_pidfile_path))
    context.signal_map = {signal.SIGTERM: sig_terminate_handler}

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
            run_daemon()
        except Exception as e:
            # will direct a traceback to the log
            logging.exception('unhandled exception, hiphub must terminate:')
            shutdown_daemon(exit_code=255)


if __name__ == '__main__':
    main()
