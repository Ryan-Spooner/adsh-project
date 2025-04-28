#!/bin/bash

# Script to run the ADSH main application, intended for use with cron.

# --- Configuration ---
# Get the absolute path to the directory containing this script
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
PROJECT_ROOT="$SCRIPT_DIR"

# Define the external data directory (MODIFY IF NEEDED ON SERVER)
export ADSH_DATA_DIR="/home/adsh-admin/adsh-data"

VENV_PATH="${PROJECT_ROOT}/venv"
PYTHON_EXEC="${VENV_PATH}/bin/python"
MAIN_SCRIPT="${PROJECT_ROOT}/src/main.py"
LOG_FILE="${ADSH_DATA_DIR}/logs/cron_run.log"

# Ensure the log directory exists
mkdir -p "$(dirname "${LOG_FILE}")"

# --- Debugging --- (Comment out for production)
# echo "--- Debugging ADSH Script Start ($(date)) ---"
# echo "[DEBUG] BASH_SOURCE[0]: ${BASH_SOURCE[0]}"
# echo "[DEBUG] dirname BASH_SOURCE[0]: $(dirname "${BASH_SOURCE[0]}")"
# echo "[DEBUG] SCRIPT_DIR: ${SCRIPT_DIR}"
# echo "[DEBUG] PROJECT_ROOT: ${PROJECT_ROOT}"
# echo "[DEBUG] VENV_PATH: ${VENV_PATH}"
# echo "[DEBUG] PYTHON_EXEC: ${PYTHON_EXEC}"
# echo "[DEBUG] MAIN_SCRIPT: ${MAIN_SCRIPT}"
# echo "--- End Debugging ---"

# --- Pre-run Checks ---
echo "--- Running ADSH Script ($(date)) --- " >> "${LOG_FILE}" 2>&1

# Check if project root exists
if [ ! -d "${PROJECT_ROOT}" ]; then
    echo "[ERROR] Project directory not found: ${PROJECT_ROOT}" >> "${LOG_FILE}" 2>&1
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "${VENV_PATH}" ] || [ ! -f "${PYTHON_EXEC}" ]; then
    echo "[ERROR] Python virtual environment not found or invalid: ${VENV_PATH}" >> "${LOG_FILE}" 2>&1
    exit 1
fi

# Check if main script exists
# Note: We check for main.py's existence, but execute via -m src.main
if [ ! -f "${MAIN_SCRIPT}" ]; then 
    echo "[ERROR] Main Python script not found: ${MAIN_SCRIPT}" >> "${LOG_FILE}" 2>&1
    exit 1
fi

# --- Execution ---
# Change to the project directory (important for .env loading and relative paths)
cd "${PROJECT_ROOT}" || {
    echo "[ERROR] Failed to change directory to ${PROJECT_ROOT}" >> "${LOG_FILE}" 2>&1
    exit 1
}

echo "[INFO] Changed directory to ${PROJECT_ROOT}" >> "${LOG_FILE}" 2>&1

# Activate virtual environment (using source is typical for interactive, but executing python directly works here)
# Execute the python script using -m flag to treat src as a package
echo "[INFO] Executing script: ${PYTHON_EXEC} -m src.main" >> "${LOG_FILE}" 2>&1

# Execute the python script, redirecting stdout and stderr
"${PYTHON_EXEC}" -m src.main >> "${LOG_FILE}" 2>&1
EXIT_CODE=$?

# --- Post-run --- 
if [ ${EXIT_CODE} -eq 0 ]; then
    echo "[INFO] Script finished successfully ($(date)). Exit code: ${EXIT_CODE}" >> "${LOG_FILE}" 2>&1
else
    echo "[ERROR] Script finished with errors ($(date)). Exit code: ${EXIT_CODE}" >> "${LOG_FILE}" 2>&1
fi

echo "--- End ADSH Script Run --- " >> "${LOG_FILE}" 2>&1

exit ${EXIT_CODE}
