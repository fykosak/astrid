FROM python:3.12

# install docker
RUN apt update && apt install -y podman containers-storage

# add astrid user
ARG DOCKER_USER=astrid
RUN useradd -m $DOCKER_USER

# change workdir
WORKDIR /app

# install python requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# install astrid under astrid user
COPY . .
RUN chown -R $DOCKER_USER:$DOCKER_USER /app
USER $DOCKER_USER

# create config directory
RUN mkdir /app/config /app/repos

ENTRYPOINT ./docker/entrypoint.sh
