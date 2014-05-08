#!/bin/bash

VERSION=`git describe HEAD --tags`
python setup.py $VERSION bdist_egg
