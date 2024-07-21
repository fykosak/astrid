from flask import session
from logger import Logger
import time
from threading import Thread, Lock
from git import Repo, Git, GitCommandError
import os
import subprocess

from auth import isLoggedIn

class Repository:
    def __init__(self, name: str, repodir: str, repoConfig: dict):
        self.name = name
        self.repodir = repodir
        self.config = repoConfig

        self.runningLock = Lock()
        self.waitingLock = Lock()
        self.logger = Logger(name)

        # validate config
        if 'git_path' not in self.config or not self.config['git_path']:
            raise ValueError(f'Config value `git_path` not specified or empty in repository {name}')
        if not isinstance(self.config['git_path'], str):
            raise TypeError(f'Config value `git_path` must be a string in repository {name}')

        if 'allowed_roles' not in self.config:
            raise ValueError(f'Config value `allowed_roles` not specified in repository {name}')
        if not isinstance(self.config['allowed_roles'], list) or not all(isinstance(role, str) for role in self.config['allowed_roles']):
            raise TypeError(f'Config value `allowed_roles` must be a list of strings in repository {name}')

        if 'build_cmd' not in self.config:
            raise ValueError(f'Config value `build_cmd` not specified in repository {name}')
        if not isinstance(self.config['build_cmd'], str):
            raise TypeError(f'Config value `build_cmd` must be a string in repository {name}')

        if 'image_version' in self.config:
            if not isinstance(self.config['image_version'], str):
                raise TypeError(f'Config value `image_version` must be a string in repository {name}')
        else:
            self.config['image_version'] = 'latest' # default value

        if 'submodules' in self.config:
            if not isinstance(self.config['submodules'], bool):
                raise TypeError(f'Config value `submodules` must be a bool in repository {name}')
        else:
            self.config['submodules'] = False # default value

    def checkAccess(self) -> bool:
        if not isLoggedIn():
            return False
        user = session['user']
        if not user['realm_access']['roles']:
            return False
        # check that user has at least one group specified in config
        if len(set(self.config['allowed_roles']).intersection(user['realm_access']['roles'])) > 0:
            return True
        return False

    def isBuilding(self) -> bool:
        return self.runningLock.locked()

    def execute(self):
        Thread(target=self._queueJob, args=(self.name, session['user']['name'])).start()

    def _queueJob(self, reponame, user):

        # if job is not running
        if self.runningLock.acquire(blocking=False):
            # lock job running and run a job
            try:
                self._runJob(reponame, user)
            finally: # ensure lock release on exception
                self.runningLock.release() # release lock for job run
            return

        # if job is already running
        if not self.waitingLock.acquire(blocking=False): # if another process is already waiting
            return # skip waiting

        # if it's not waiting, waiting lock is acquired

        # wait for previos job to complete, wait for running lock release and acquire it
        self.runningLock.acquire()
        self.waitingLock.release() # relase lock for waiting
        try:
            self._runJob(reponame, user) # run job
        finally: # ensure lock release on exception
            self.runningLock.release() # release lock for job run

    def _runJob(self, reponame, user):
        msg = None
        sendMail = False

        time_start = time.time()
        time_end = None

        try:
            repo = self._updateRepo(reponame)
            try:
                if self._build(reponame):
                    msg = f"#{repo.head.commit.hexsha[0:6]} Build succeeded."
                    time_end = time.time()
                else:
                    msg = f"#{repo.head.commit.hexsha[0:6]} Build failed."
                    time_end = time.time()
            except:
                msg = f"#{repo.head.commit.hexsha[0:6]} Build error."
                raise
        except GitCommandError as e:
            msg = f"Pull error. ({e})"
            sendMail = True
            raise

        if time_end is not None:
            msg += " ({:.2f} s)".format(time_end - time_start)

        self.logger.log(user, msg, sendMail)

    def _updateRepo(self, reponame):
        remotepath = self.config['git_path']
        submodules = self.config['submodules'] if 'submodules' in self.config else False
        localpath = os.path.join(self.repodir, reponame)

        os.umask(0o007) # create repo content not readable to others
        if not os.path.isdir(localpath):
            print(f"Repository {reponame} empty, cloning")
            g = Git()
            g.clone(remotepath, localpath)

            repo = Repo(localpath)

            if submodules:
                repo.git.submodule("init")

            # not-working umask workaround
            subprocess.run(["chmod", "g+w", localpath], check=False)
        else:
            print(f"Pulling repository {reponame}")
            repo = Repo(localpath)
            try:
                repo.git.update_index("--refresh")
            except GitCommandError:
                pass # it's fine, we'll reset
            # We use wrapped API (direct git command calls) rather than calling semantic GitPython API.
            # (e.g. repo.remotes.origin.pull() was replaced by repo.git.pull("origin"))
            repo.git.reset("--hard", "master")
            #repo.git.clean("-f")
            repo.git.pull("origin")

            if submodules:
                repo.git.submodule("init")
                repo.git.submodule("foreach", "git", "fetch")
                repo.git.submodule("update")

        return repo

    def _build(self, reponame):
        cmd = self.config['build_cmd']
        cwd = os.path.join(self.repodir, reponame) # current working directory
        image_version = self.config['image_version']

        print(f"Building {reponame}")
        logfilename = os.path.expanduser(f"/data/log/{reponame}.build.log")
        logfile = open(logfilename, "w")
        p = subprocess.run(["docker", "run", "--rm", "-v", f"{cwd}:/usr/src/local", f"--user={os.getuid()}:{os.getgid()}",  f"fykosak/buildtools:{image_version}"] + cmd.split(), cwd=cwd, stdout=logfile, stderr=logfile, check=False)
        logfile.close()
        print(f"Building {reponame} completed")
        return p.returncode == 0
