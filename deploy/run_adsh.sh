#!/bin/bash

# Script to run the ADSH main application.
# Intended for manual testing or execution via systemd on the deployment server.
# ASSUMES THIS SCRIPT IS LOCATED IN THE PROJECT ROOT DIRECTORY.

# --- Configuration ---
# Determine the absolute path of the project root (where this script lives)
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# --- CRITICAL: Set the correct external data directory path on the server ---
# This directory contains .env, logs, recordings, etc.
export ADSH_DATA_DIR="/home/adsh-admin/adsh-data" # <<<--- VERIFY/EDIT THIS PATH

VENV_PATH="${PROJECT_ROOT}/venv"
PYTHON_EXEC="${VENV_PATH}/bin/python"
MAIN_MODULE="src.main" # Execute as a module

echo "--- Starting ADSH Script ($(date)) ---"
echo "[INFO] Project Root: ${PROJECT_ROOT}"
echo "[INFO] Data Directory (ADSH_DATA_DIR): ${ADSH_DATA_DIR}"
echo "[INFO] Python Executable: ${PYTHON_EXEC}"

# --- Pre-run Checks ---

# Check if virtual environment exists
if [ ! -d "${VENV_PATH}" ] || [ ! -f "${PYTHON_EXEC}" ]; then
    echo "[ERROR] Python virtual environment not found or invalid: ${VENV_PATH}" >&2
    echo "[ERROR] Ensure 'venv' directory exists in ${PROJECT_ROOT}" >&2
    exit 1
fi

# Check if the main source directory exists (as a proxy for project structure)
if [ ! -d "${PROJECT_ROOT}/src" ]; then
    echo "[ERROR] Source directory not found: ${PROJECT_ROOT}/src" >&2
    exit 1
fi

# Check if the data directory exists (important for .env loading by Python)
if [ ! -d "${ADSH_DATA_DIR}" ]; then
    echo "[ERROR] Data directory ADSH_DATA_DIR not found: ${ADSH_DATA_DIR}" >&2
    echo "[ERROR] Please create this directory or update the path in this script." >&2
    exit 1
fi

# Check if the .env file exists in the project root directory
# Note: Python code will automatically load it from here if found.
if [ ! -f "${PROJECT_ROOT}/.env" ]; then
    echo "[ERROR] Required .env file not found in project root: ${PROJECT_ROOT}/.env" >&2
    echo "[ERROR] Please ensure the .env file exists in the project root on the server." >&2
    # Exit because config is essential
    exit 1
fi


# --- Execution ---
# Change to the project directory (redundant if already there, but safe)
cd "${PROJECT_ROOT}" || {
    echo "[ERROR] Failed to change directory to ${PROJECT_ROOT}" >&2
    exit 1
}
echo "[INFO] Current working directory: $(pwd)" # Should be PROJECT_ROOT

# Execute the python script using -m flag
# Output (stdout/stderr) will go directly to terminal (or journald if run by systemd)
echo "[INFO] Executing Python module: ${PYTHON_EXEC} -m ${MAIN_MODULE}"
"${PYTHON_EXEC}" -m ${MAIN_MODULE}
EXIT_CODE=$?

# --- Post-run ---
if [ ${EXIT_CODE} -eq 0 ]; then
    echo "[INFO] Script finished successfully ($(date)). Exit code: ${EXIT_CODE}"
else
    echo "[ERROR] Script finished with errors ($(date)). Exit code: ${EXIT_CODE}" >&2
fi

echo "--- End ADSH Script Run ---"

exit ${EXIT_CODE}
