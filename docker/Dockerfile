FROM python:3.12

# install docker
RUN apt update && apt install -y podman containers-storage

# change workdir
WORKDIR /app

# install python requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# copy ssh config
COPY ./docker/ssh.conf /etc/ssh/ssh_config.d/99-astrid.conf
COPY ./docker/sshd.conf /etc/ssh/sshd_config.d/99-astrid.conf

# copy containers config
COPY ./docker/libpod.conf /etc/containers/libpod.conf
COPY ./docker/storage.conf /etc/containers/storage.conf

# install astrid
COPY . .

ENTRYPOINT ./docker/entrypoint.sh
