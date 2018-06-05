#!/bin/bash

VERSION=`git describe HEAD --tags`
python3 setup.py $VERSION bdist_egg
