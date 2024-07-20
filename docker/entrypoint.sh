#!/bin/bash

set -e

function checksubid {
	if [ $(grep -E "^$1:" $2 | wc -l) -eq 0 ]; then
		exit 1
	fi
	exit 0
}

# check required variables
if [ -z "$PUID" ]; then
	echo 'Environment variable $PUID not specified'
	exit 1
fi

if [ -z "$GUID" ]; then
	echo 'Environment variable $GUID not specified'
	exit 1
fi

# create astrid user and group
if [ ! $(getent group astrid) ] && [ ! $(getent group $GUID) ]; then
	groupadd --gid $GUID astrid
	echo "Group astrid with GID $GUID created."
fi
if [ ! $(getent passwd astrid) ] && [ ! $(getent passwd $PUID) ]; then
	useradd --uid $PUID --gid $GUID --create-home --add-subids-for-system astrid
	echo "User astrid with UID $PUID created."
fi

USER=$(id -nu $PUID)
usermod -a -G docker $USER

# add to subuid and subgid
if ! $(checksubid $USER /etc/subuid); then
	echo "$USER:100000:65536" >> /etc/subuid
fi

if ! $(checksubid $USER /etc/subgid); then
	echo "$USER:100000:65536" >> /etc/subgid
fi

# set ownership of /data to target user
chown "$PUID:$GUID" /data


# create needed files if missing
su - $USER -c "mkdir -p /data/config /data/containers /data/log /data/repos /data/ssh"

su - $USER -c "cp -n /app/config.toml.sample /data/config/config.toml"
su - $USER -c "cp -n /app/repos.toml.sample  /data/config/repos.toml"

if [ $(ls "/data/ssh" | grep ".pub" | wc -l) -eq 0 ]; then
	su - $USER -c "ssh-keygen -t ed25519 -f /data/ssh/id_ed25519"
fi

dockerd &
if [ "$MODE" == "development" ]; then
	su - $USER -c "python3 -u /app/src/app.py"
else
	su - $USER -c "gunicorn --config /app/src/gunicorn.conf.py --chdir /app/src"
fi
