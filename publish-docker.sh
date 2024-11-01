#!/bin/bash
# Runs a Docker build here

VER=`git describe --tags --abbrev=0`

echo Getting latest tags
git pull upstream --tags

echo Pushing to $VER ...
docker login
docker build -t dribdat/dribdat:$VER .
docker push dribdat/dribdat:$VER
docker tag dribdat/dribdat:$VER dribdat/dribdat:latest
docker push dribdat/dribdat:latest
echo Done!
