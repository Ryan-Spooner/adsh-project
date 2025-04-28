#!/bin/bash

# Display instructions for adding NTFY users via Podman

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
source "${SCRIPT_DIR}/config.sh"

echo "--> Use this command INTERACTIVELY in your terminal to add users and set passwords."
echo "    Run this *before* starting the server if you need to create users."
echo "    Replace USERNAME and ROLE as needed (e.g., admin, user)."
echo "    Ensure the config directory exists: ${HOST_CONFIG_DIR}"

echo ""
echo "   podman run --rm -it \\"
echo "     -v \"${HOST_CONFIG_DIR}:${CONTAINER_CONFIG_DIR}:Z\" \\"
echo "     \"${IMAGE_NAME}\" \\"
echo "     user add <USERNAME> --role=<ROLE>"
echo ""
echo "    Example publisher: podman run --rm -it -v \"${HOST_CONFIG_DIR}:${CONTAINER_CONFIG_DIR}:Z\" \"${IMAGE_NAME}\" user add ${DEFAULT_PUBLISHER_USER} --role=user"
echo "    Example client:    podman run --rm -it -v \"${HOST_CONFIG_DIR}:${CONTAINER_CONFIG_DIR}:Z\" \"${IMAGE_NAME}\" user add ${DEFAULT_CLIENT_USER} --role=user"
echo ""

exit 0
