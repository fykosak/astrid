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

$1 = "localhost:8000"
$2 = "/build/$REPOSITORY_BASENAME"

REQUEST="HEAD $2 HTTP/1.0\r
Host: $1\r
Authorization: Basic $AUTH\r
\r
" 
echo -ne "$REQUEST" | nc -q 1 ${1/:/ }
