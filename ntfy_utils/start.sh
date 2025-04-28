#!/bin/bash

# Start the NTFY Podman container

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
source "${SCRIPT_DIR}/config.sh"

check_config
echo "--> Attempting to start NTFY container '${CONTAINER_NAME}'..."

# Ensure the container doesn't already exist (remove if stopped or force remove if running)
if podman container exists "${CONTAINER_NAME}"; then
    echo "--> Found existing container '${CONTAINER_NAME}'. Stopping and removing..."
    podman stop "${CONTAINER_NAME}" > /dev/null 2>&1 || echo "    - Warning: Container already stopped or failed to stop."
    podman rm "${CONTAINER_NAME}" > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "    - ERROR: Failed removing existing container '${CONTAINER_NAME}'. Please check manually ('podman ps -a')."
        exit 1
    fi
    echo "--> Existing container removed."
fi

# Create named volume if it doesn't exist
echo "--> Ensuring cache volume '${CACHE_VOLUME}' exists..."
podman volume create "${CACHE_VOLUME}" > /dev/null 2>&1 || true 

echo "--> Starting new container '${CONTAINER_NAME}' listening on 127.0.0.1:${HOST_PORT}"
podman run -d \
    --name "${CONTAINER_NAME}" \
    --restart=unless-stopped \
    -p "127.0.0.1:${HOST_PORT}:${CONTAINER_PORT}" \
    -v "${CACHE_VOLUME}:${CONTAINER_CACHE_DIR}:Z" \
    -v "${HOST_CONFIG_DIR}:${CONTAINER_CONFIG_DIR}:Z" \
    "${IMAGE_NAME}" \
    serve --config "${CONTAINER_CONFIG_DIR}/server.yml"

EXIT_CODE=$?
if [ ${EXIT_CODE} -eq 0 ]; then
  echo "--> Podman command executed. Container starting in background."
  echo "--> Check status with: ./status.sh"
  echo "--> View logs with:  ./logs.sh"
  echo "--> Caddy should proxy external requests from your domain to 127.0.0.1:${HOST_PORT}"
else
  echo "--> Podman command failed (Exit Code: ${EXIT_CODE}). Check for errors above."
  echo "    Common issues: Incorrect paths in HOST_CONFIG_DIR, permission problems, Podman issues."
fi

exit ${EXIT_CODE}
