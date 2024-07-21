#!/bin/bash

# Astrid connection configuration
USER=<user>
PASS=<password>
URL="https://<url>/build/$GITEA_REPO_NAME"

curl --silent --output /dev/null --user $USER:$PASS $URL \
&& echo "$GITEA_REPO_NAME: rebuild request sent to Astrid." \
|| echo "$GITEA_REPO_NAME: rebuild request sending failed."
