#!/bin/bash

# Show status of the NTFY Podman container

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
source "${SCRIPT_DIR}/config.sh"

echo "--> Checking status for container '${CONTAINER_NAME}'..."
podman ps -a -f name="${CONTAINER_NAME}"

exit $?
