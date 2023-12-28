#!/bin/bash

DATA_OWNER=$(stat -c '%u' /data)

if [ "$DATA_OWNER" -ne "$UID" ]; then
	echo "Directory 'data' not owned by target user with $UID, instead owned by user with uid $DATA_OWNER"
	exit 1
fi

mkdir -p /data/config /data/containers /data/log /data/repos /data/ssh

cp -n /app/config.ini.sample /data/config/config.ini
cp -n /app/repos.ini.sample  /data/config/repos.ini

if [ $(ls "/data/ssh" | grep ".pub" | wc -l) -eq 0 ]; then
	ssh-keygen -t ed25519 -f /data/ssh/id_ed25519
fi

python3 -u ./main
