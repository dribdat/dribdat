#!/bin/bash
# Runs a Docker build here

echo Pushing to dev tag ...
docker login
docker build -t dribdat/dribdat:dev .
docker push dribdat/dribdat:dev
echo Done!
