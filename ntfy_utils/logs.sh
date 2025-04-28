#!/bin/bash

# Show logs of the NTFY Podman container

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
source "${SCRIPT_DIR}/config.sh"

echo "--> Showing logs for '${CONTAINER_NAME}' (use -f for follow, Ctrl+C to stop)..."
podman logs "${CONTAINER_NAME}" "$@" # Pass any arguments (like -f) to podman logs

exit $?
