#!/bin/bash

if [ $(git rev-parse --is-bare-repository) = true ]
then
	REPOSITORY_BASENAME=$(basename $(readlink -nf "$PWD"/..))
	REPOSITORY_BASENAME=${REPOSITORY_BASENAME%.git}
else
	REPOSITORY_BASENAME=$(basename $(readlink -nf "$PWD"/../..))
fi

echo $REPOSITORY_BASENAME

USER=user
PWD=pwd

AUTH=$(echo -n "$USER:$PWD" | base64)

HOST="localhost:8000"
PATH="/build/$REPOSITORY_BASENAME"

REQUEST="HEAD $PATH HTTP/1.0\r
Host: $HOST\r
Authorization: Basic $AUTH\r
\r
" 
#echo -ne "$REQUEST" | netcat -q 1 ${HOST/:/ }
echo -ne "$REQUEST" | /bin/nc.traditional -q 1 ${HOST/:/ }
