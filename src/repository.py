from flask import session
from logger import Logger
import time
from datetime import datetime
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

        if 'archived' in self.config:
            if not isinstance(self.config['archived'], bool):
                raise TypeError(f'Config value `archived` must be a bool in repository {name}')
        else:
            self.config['archived'] = False # default value


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
        """
            Queue a job run.

            If no job is running for repository, exclusive lock is obtained
            and job is executed. If another job is already running, lock for
            waiting and job is waiting for first job to finish, then runs.
            If one job is running and second is waiting, job run is skipped
            as git pull of the waiting job will update to the newest state
            of repository anyway.
        """
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
        """
            Run a build job

            The repository is pulled first, than build is started.
        """
        msg = None
        sendMail = False

        time_start = time.time()
        time_end = None

        try:
            repo = self._updateRepo(reponame)
            try:
                if self._build(reponame):
                    msg = f"#{repo.head.commit.hexsha[:8]} Build succeeded."
                    time_end = time.time()
                else:
                    msg = f"#{repo.head.commit.hexsha[0:8]} Build failed."
                    time_end = time.time()
            except:
                msg = f"#{repo.head.commit.hexsha[0:8]} Build error."
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

    @staticmethod
    def _format_time_ago(time_str):
        try:
            time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")
            now = datetime.now()
            diff = now - time

            if diff.days > 0:
                if diff.days == 1:
                    return "1 day ago"
                return f"{diff.days} days ago"
            elif diff.seconds >= 3600:
                hours = diff.seconds // 3600
                if hours == 1:
                    return "1 hour ago"
                return f"{hours} hours ago"
            elif diff.seconds >= 60:
                minutes = diff.seconds // 60
                if minutes == 1:
                    return "1 minute ago"
                return f"{minutes} minutes ago"
            else:
                return "just now"
        except ValueError:
            return time_str # orig if parse fails
        
    def get_commit_info(self, commit_hash):
        localpath = os.path.join(self.repodir, self.name)
        repo = Repo(localpath)
        commit = repo.commit(commit_hash)
        commit_msg = commit.message.strip().split('\n')[0]
        commit_author = commit.author.name
        commit_url = f"https://git.fykos.cz/FYKOS/{self.name}/commit/{commit.hexsha}"
        return commit_msg, commit_author, commit_url

    def get_current_build_status(self):
        records = self.logger.getLogs()
        if len(records) == 0: 
            return {"status": "unknown", "timeinfo": "", "user": ""}

        last_record = records[0]
        
        if "Build failed." in last_record[1]:
            status = "failed"
            for record in records:
                if "Build succeeded." in record[1]:
                    break
                if "Build failed." in record[1]:
                    last_record = record
        elif "Build succeeded." in last_record[1]:
            status = "succeeded"
        else:
            status = "unknown"
        
        commit_hash = last_record[1].split()[0][1:]
        try:
            commit_msg, commit_author, commit_url = self.get_commit_info(commit_hash)
            return {
                "status": status,
                "timeinfo": f"- {self._format_time_ago(last_record[0])}",
                "commit": f" - <a href='{commit_url}' target='_blank' class='link-pink'>#{commit_hash}</a>: {commit_msg} (by {commit_author})"
            }
        except Exception as e:
            return {
                "status": status,
                "timeinfo": f"- {self._format_time_ago(last_record[0])}",
                "commit": ""
            }        
