FROM python:3.12

# install docker
RUN apt update && apt install -y podman containers-storage

# add astrid user
ARG DOCKER_USER=astrid
RUN useradd -m $DOCKER_USER

# change workdir
WORKDIR /data/

# install python requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# install astrid under astrid user
COPY . .
RUN chown -R $DOCKER_USER:$DOCKER_USER /data
USER $DOCKER_USER
#RUN ./build.sh

# create config directory
RUN mkdir ~/.astrid

ENTRYPOINT ./docker/entrypoint.sh
