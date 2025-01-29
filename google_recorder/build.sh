#!/bin/bash

# Detect platform
PLATFORM=$(uname -m)
if [ "$PLATFORM" = "arm64" ] || [ "$PLATFORM" = "aarch64" ]; then
    DOCKER_PLATFORM="linux/arm64"
else
    DOCKER_PLATFORM="linux/amd64"
fi

# Build the Docker image
docker build --platform $DOCKER_PLATFORM -t google-meet-recorder .

# Get the absolute paths for volume mounts
RECORDINGS_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/recordings"
SESSION_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.session"

# Run the container with necessary volume mounts
docker run -it \
    --name google-meet-recorder \
    --rm \
    --platform $DOCKER_PLATFORM \
    -v "${RECORDINGS_PATH}:/app/recordings" \
    -v "${SESSION_PATH}:/app/.session" \
    -e DISPLAY=:${X_SERVER_NUM:-1}.0 \
    --env-file .env \
    --shm-size=2g \
    google-meet-recorder "$@" 