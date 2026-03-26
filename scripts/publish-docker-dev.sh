#!/bin/bash
# Runs a Docker build here

echo Pushing to dev tag ...
podman build -t dribdat/dribdat:dev .
podman push dribdat/dribdat:dev
echo Done!
