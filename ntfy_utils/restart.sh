#!/bin/bash

# Restart the NTFY Podman container

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

echo "--> Restarting NTFY server..."

"${SCRIPT_DIR}/stop.sh"

if [ $? -ne 0 ]; then
    echo "--> Stop command reported an issue, but attempting start anyway..." 
fi

sleep 3 # Give it a moment to stop cleanly

"${SCRIPT_DIR}/start.sh"

EXIT_CODE=$?
if [ ${EXIT_CODE} -eq 0 ]; then
    echo "--> Restart sequence initiated."
else
    echo "--> Start command failed during restart." >&2
fi

exit ${EXIT_CODE}
