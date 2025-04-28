#!/bin/bash

# Remove the NTFY Podman container

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
source "${SCRIPT_DIR}/config.sh"

echo "--> Removing container '${CONTAINER_NAME}' (stopping it first if running)..."
podman stop "${CONTAINER_NAME}" >/dev/null 2>&1 || true # Ignore error if already stopped
podman rm "${CONTAINER_NAME}"

EXIT_CODE=$?
if [ ${EXIT_CODE} -ne 0 ]; then
  echo "--> Warning: Failed to remove container (maybe already removed?)" >&2
fi

exit ${EXIT_CODE}
