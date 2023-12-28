#!/bin/bash

set -e

# check required variables
if [ -z "$PUID" ]; then
	echo 'Environment variable $PUID not specified'
	exit 1
fi

if [ -z "$GUID" ]; then
	echo 'Environment variable $PUID not specified'
	exit 1
fi

# create astrid user and group
if [ ! $(getent group astrid) ]; then
	groupadd --gid $GUID astrid
	echo "Group astrid with GID $GUID created."
fi
if [ ! $(getent passwd astrid) ]; then
	useradd --uid $PUID --gid $GUID --create-home --add-subids-for-system astrid
	echo "User astrid with UID $PUID created."
fi

# set ownership of /data to target user
chown "$PUID:$GUID" /data

# create needed files if missing
su - astrid -c "mkdir -p /data/config /data/containers /data/log /data/repos /data/ssh"

su - astrid -c "cp -n /app/config.ini.sample /data/config/config.ini"
su - astrid -c "cp -n /app/repos.ini.sample  /data/config/repos.ini"

if [ $(ls "/data/ssh" | grep ".pub" | wc -l) -eq 0 ]; then
	su - astrid -c "ssh-keygen -t ed25519 -f /data/ssh/id_ed25519"
fi

su - astrid -c "python3 -u /app/main"
