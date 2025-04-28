#!/bin/bash

# Stop the NTFY Podman container

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
source "${SCRIPT_DIR}/config.sh"

echo "--> Stopping container '${CONTAINER_NAME}'..."
podman stop "${CONTAINER_NAME}"

EXIT_CODE=$?
if [ ${EXIT_CODE} -ne 0 ]; then
  echo "--> Warning: Failed to stop container (maybe already stopped?)" >&2
fi

exit ${EXIT_CODE}
