#!/bin/bash

if [ $(git rev-parse --is-bare-repository) = true ]
then
	REPOSITORY_BASENAME=$(basename "$PWD") 
	REPOSITORY_BASENAME=${REPOSITORY_BASENAME%.git}
else
	REPOSITORY_BASENAME=$(basename $(readlink -nf "$PWD"/..))
fi

USER=user
PWD=pwd

AUTH=$(echo -n "$USER:$PWD" | base64)

PATH="localhost:8000"
HOST="/build/$REPOSITORY_BASENAME"

REQUEST="HEAD $PATH HTTP/1.0\r
Host: $HOST\r
Authorization: Basic $AUTH\r
\r
" 
echo -ne "$REQUEST" | nc -q 1 ${1/:/ }
