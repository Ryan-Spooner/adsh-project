import os
import datetime
from dotenv import load_dotenv
import google.generativeai as genai

RECORDINGS_DIR = "recordings" # Directory to save recordings
LOG_DIR = "log" # Directory for log file

# --- Configuration Loading ---
def load_config():
    """Load environment variables from .env file and return them."""
    load_dotenv()  # Load variables from .env
    config = {
        "twilio_account_sid": os.getenv("TWILIO_ACCOUNT_SID"),
        "twilio_auth_token": os.getenv("TWILIO_AUTH_TOKEN"),
        "twilio_phone_number": os.getenv("TWILIO_PHONE_NUMBER"),
        "hotline_phone_number": os.getenv("HOTLINE_PHONE_NUMBER"),
        "personal_phone_number": os.getenv("PERSONAL_PHONE_NUMBER"),
        "google_api_key": os.getenv("GOOGLE_API_KEY"),
        "target_color": os.getenv("TARGET_COLOR", "blue").lower(),
        "log_file": os.path.join(LOG_DIR, "adsh_log.md"), # Use LOG_DIR constant
        "recordings_dir": RECORDINGS_DIR, # Add recordings dir to config
        # NTFY Configuration
        "ntfy_server_url": os.getenv("NTFY_SERVER_URL"),
        "ntfy_topic_alerts": os.getenv("NTFY_TOPIC_ALERTS"), # Specific topic for alerts
        "ntfy_topic_logs": os.getenv("NTFY_TOPIC_LOGS"),   # Specific topic for logs
        "ntfy_topic_errors": os.getenv("NTFY_TOPIC_ERRORS"), # Specific topic for errors
        "ntfy_username": os.getenv("NTFY_USERNAME"),
        "ntfy_password": os.getenv("NTFY_PASSWORD"),
    }
    # --- Refined Configuration Validation ---
    required_keys = [
        "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER",
        "HOTLINE_PHONE_NUMBER", "GOOGLE_API_KEY", # Keep PERSONAL_PHONE_NUMBER optional
        "NTFY_SERVER_URL", "NTFY_TOPIC_ALERTS", "NTFY_TOPIC_LOGS", "NTFY_TOPIC_ERRORS",
        "NTFY_USERNAME", "NTFY_PASSWORD"
        # TARGET_COLOR has a default; LOG_FILE and RECORDINGS_DIR are derived
    ]
    missing_keys = []
    for key in required_keys:
        # Check if the key exists in os.environ after load_dotenv OR if the loaded value is empty
        # Use os.getenv directly here as 'config' dict might have None values from getenv
        if not os.getenv(key):
            missing_keys.append(key)

    if missing_keys:
        raise ValueError(
            f"Missing or empty required environment variables: {', '.join(missing_keys)}. "
            f"Please check your .env file."
        )
    # ------------------------------------

    # Ensure recordings directory exists
    recordings_dir = config.get("recordings_dir")
    if not os.path.exists(recordings_dir):
        try:
            os.makedirs(recordings_dir)
            print(f"   Created directory: {recordings_dir}")
        except OSError as e:
            raise ValueError(f"Could not create recordings directory '{recordings_dir}': {e}")

    # Ensure log directory exists
    log_file_path = config['log_file']
    log_dir_path = os.path.dirname(log_file_path)
    if log_dir_path and not os.path.exists(log_dir_path):
        try:
            os.makedirs(log_dir_path)
            print(f"   Created directory: {log_dir_path}")
        except OSError as e:
            # Avoid raising error if dir already exists due to race condition
            if not os.path.isdir(log_dir_path):
                 raise ValueError(f"Could not create log directory '{log_dir_path}': {e}")

    # Configure Google API Key
    if config['google_api_key']:
        genai.configure(api_key=config['google_api_key'])
    else:
        raise ValueError("Missing environment variable: GOOGLE_API_KEY")
    return config
