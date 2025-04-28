#!/bin/bash

# Shared configuration for NTFY utility scripts

# --- Server Configuration --- 
# MODIFY THESE PATHS AND NAMES TO MATCH YOUR SERVER SETUP
CONTAINER_NAME="ntfy-adsh"                  # Name for the Podman container
HOST_CONFIG_DIR="/home/adsh-admin/adsh-data/config/ntfy" # ABSOLUTE path to NTFY config dir on server
HOST_PORT="8080"                             # Localhost port NTFY listens on (Caddy proxies TO this)

# --- Container/Image Configuration --- 
CONTAINER_PORT="80"                          # Port inside the container (NTFY default)
CONTAINER_CONFIG_DIR="/etc/ntfy"             # Config directory inside the container
CONTAINER_CACHE_DIR="/var/cache/ntfy"        # Cache directory inside the container
CACHE_VOLUME="ntfy_adsh_cache"               # Named volume for the message cache
IMAGE_NAME="docker.io/binwiederhier/ntfy"  # Use latest or pin a specific version

# --- Default Usernames (for adduser command) ---
DEFAULT_PUBLISHER_USER="adsh_publisher"
DEFAULT_CLIENT_USER="ryans_client"

# --- Helper Functions ---
check_config() {
  echo "--> Checking configuration..."
  if [ ! -d "${HOST_CONFIG_DIR}" ]; then
    echo "ERROR: Host configuration directory not found: ${HOST_CONFIG_DIR}"
    echo "       Please create it and place server.yml and user.db inside."
    exit 1
  fi
  if [ ! -f "${HOST_CONFIG_DIR}/server.yml" ]; then
    echo "ERROR: Configuration file not found: ${HOST_CONFIG_DIR}/server.yml"
    exit 1
  fi
  echo "--> Configuration check passed."
}
