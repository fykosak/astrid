FROM python:3.12

# tells entrypoint if it's a production or development environment
# and should run gunicorn or not
ENV MODE="production"

# install docker
RUN apt update && apt install -y docker.io containers-storage

# change workdir
WORKDIR /app

# install python requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# copy ssh config
COPY ./docker/ssh.conf /etc/ssh/ssh_config.d/99-astrid.conf
COPY ./docker/sshd.conf /etc/ssh/sshd_config.d/99-astrid.conf

# copy containers config
COPY ./docker/daemon.json /etc/docker/daemon.json

# install astrid
COPY . .

ENTRYPOINT ./docker/entrypoint.sh
