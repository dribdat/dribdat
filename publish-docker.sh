#!/bin/bash
# Runs a Docker build here

VER=`git describe --tags --abbrev=0`

echo Getting latest tags
git pull upstream --tags

echo Pushing to $VER ...
docker login
docker build -t loleg/dribdat:$VER .
docker push loleg/dribdat:$VER
docker tag loleg/dribdat:$VER loleg/dribdat:latest
docker push loleg/dribdat:latest
echo Done!
