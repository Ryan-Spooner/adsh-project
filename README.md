# Automated Drug Screen Hotline (ADSH)

This project automates the process of calling a drug screen hotline, analyzing the recorded message using AI, and sending push notifications with the relevant scheduling information.

## Features

*   **Automated Calling:** Places calls to the hotline using Twilio.
*   **Call Recording:** Records the audio message from the hotline.
*   **AI Analysis:** Uses Google Gemini to analyze scheduling details.
*   **Push Notifications:** Sends results to the user via a self-hosted NTFY server.
*   **Modular Structure:** Code organized into logical modules (`config_loader`, `telephony`, `audio_analyzer`, `logger`, `notifier`).
*   **Scheduling:** Uses `systemd` timers for reliable execution on Linux server.
*   **Secure Configuration:** Uses a `.env` file for sensitive credentials.
*   **HTTPS:** NTFY server exposed securely via HTTPS using Caddy reverse proxy.

## Technology Stack

*   **Python 3.12**
*   **Modules:** `twilio`, `google-generativeai`, `python-dotenv`, `requests`
*   **Telephony:** Twilio
*   **AI:** Google Gemini API
*   **Notifications:** NTFY (Self-Hosted)
*   **Scheduling:** Systemd Timers (on Linux deployment target)
*   **Web Server/Proxy:** Caddy (for NTFY HTTPS)
*   **Containerization:** Podman (for running NTFY server)
*   **Deployment Target:** Linux VPS (e.g., Linode)

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <adsh-project-url>
    cd adsh-project
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3.12 -m venv venv # Ensure you have Python >= 3.12 installed
    source venv/bin/activate # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    *   Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file and fill in your actual credentials:
        *   `TWILIO_ACCOUNT_SID`: Your Twilio Account SID.
        *   `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token.
        *   `TWILIO_PHONE_NUMBER`: Your Twilio phone number.
        *   `HOTLINE_PHONE_NUMBER`: The drug screen hotline number.
        *   `GOOGLE_API_KEY`: Your Google AI API key.
        *   `NTFY_BASE_URL`: Base URL of your NTFY server (e.g., `https://adsh.info`).
        *   `NTFY_TOPIC_LOGS`: Topic name for general logs (e.g., `adsh_logs`).
        *   `NTFY_TOPIC_ALERTS`: Topic name for positive results/alerts (e.g., `adsh_alerts`).
        *   `NTFY_TOPIC_ERRORS`: Topic name for error notifications (e.g., `adsh_errors`).
        *   `NTFY_ADMIN_USER`: (Optional) Admin username for your NTFY server.
        *   `NTFY_ADMIN_PASS`: (Optional) Admin password for your NTFY server.
        *   `TARGET_COLOR`: (Optional) Specific color to look for (defaults to "blue", case-insensitive).
        *   `AUDIO_ANALYSIS_PROMPT`: (Optional) Override the default Gemini prompt.

## Usage (Local Development)

Execute the main script directly:

```bash
# Ensure .env file is populated and venv is active
python -m src.main
```

The script will:
1.  Load configuration from `.env` via `config_loader`.
2.  Use `telephony` module to call the hotline, record, and download.
3.  Save recording locally (ignored by git).
4.  Use `audio_analyzer` module to send recording to Gemini.
5.  Parse the analysis result.
6.  Use `notifier` module to send notifications/logs to NTFY topics.
7.  Use `logger` module to append results to the local log file (`log/poc_log.md`).
8.  Use `telephony` module to delete the recording from Twilio.

## Deployment (Linux Server)

This application is designed to be deployed on a Linux server (e.g., Linode running Ubuntu) using `systemd` for scheduling and Podman/Caddy for the NTFY server.

**Server Setup Overview:**

1.  **Provision Server:** Set up a Linux VPS (e.g., Ubuntu LTS on Linode).
2.  **Create User:** Create a non-root user with `sudo` privileges (e.g., `adsh-admin`).
3.  **Install Dependencies:** Install `python3.12`, `python3.12-venv`, `git`, `podman`, `caddy`.
4.  **Configure DNS:** Point your domain (e.g., `adsh.info`) 'A' record to the server's IP. Set Reverse DNS (rDNS) in your VPS provider's panel.
5.  **Configure Firewall:** Ensure ports 22 (SSH), 80 (HTTP), and 443 (HTTPS) are open (`ufw allow ssh/http/https`).
6.  **Install Caddy:** Install Caddy and configure `/etc/caddy/Caddyfile` to reverse proxy your domain to the NTFY container's local port, enabling automatic HTTPS.
7.  **Install NTFY:** Run the NTFY server using Podman, binding to a localhost port (e.g., `127.0.0.1:8080`), and mounting configuration (`server.yml`, `user.db`) and cache volumes.
8.  **Deploy Application Code:** Clone the repository onto the server (e.g., `/home/adsh-admin/adsh-project`).
9.  **Setup Python Environment:** Create a virtual environment, install dependencies (`pip install -r requirements.txt`).
10. **Configure `.env`:** Create and populate the `.env` file on the server with production values.
11. **Setup Systemd Timer:** Configure and enable the systemd timer (see below).

**Scheduling (Systemd Timers)**

Instead of `cron`, we use `systemd` timers for reliability and better logging.

1.  **Unit Files:** The `deploy/systemd/` directory contains template unit files:
    *   `adsh-runner.service`: Defines *how* to run the script (user, working directory, command).
    *   `adsh-runner.timer`: Defines *when* to run the service (e.g., daily at specific times).

2.  **Deployment Steps:**
    *   Copy the `.service` and `.timer` files from `deploy/systemd/` to `/etc/systemd/system/` on the server.
    *   **Edit the files in `/etc/systemd/system/`:** Replace placeholders like `User=`, `Group=`, `WorkingDirectory=`, and `ExecStart=` with the correct values for your server environment (e.g., `User=adsh-admin`, `WorkingDirectory=/home/adsh-admin/adsh-project`, `ExecStart=/home/adsh-admin/adsh-project/venv/bin/python -m src.main`).
    *   Ensure the `run_adsh.sh` script (if used by the service file) has execute permissions (`chmod +x run_adsh.sh`). *Note: The current service file template executes python directly.* 
    *   Reload the systemd daemon to recognize the new files:
        ```bash
        sudo systemctl daemon-reload
        ```
    *   Enable and start the timer (it will automatically trigger the service according to its schedule):
        ```bash
        sudo systemctl enable --now adsh-runner.timer
        ```

3.  **Checking Status & Logs:**
    *   Check timer status: `systemctl status adsh-runner.timer`
    *   List timers: `systemctl list-timers --all`
    *   View service logs: `journalctl -u adsh-runner.service` (use `-f` to follow logs)

## Future Development / Backlog

*   [ContainerizeApp] - Containerize the main Python application using Podman.
*   [Testing] - Review and implement unit/integration tests for Python modules.
*   Refine Gemini prompt for more robust extraction.
*   Consider adding state management (e.g., avoid re-processing if already run for the day).
