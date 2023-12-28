FROM python:3.12

# install docker
RUN apt update && apt install -y podman containers-storage

# add astrid user
ARG DOCKER_USER=astrid
RUN useradd -m $DOCKER_USER
RUN chmod 777 /home

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

# install astrid under astrid user
COPY . .
RUN chown -R $DOCKER_USER:$DOCKER_USER /app
USER $DOCKER_USER

ENTRYPOINT ./docker/entrypoint.sh
