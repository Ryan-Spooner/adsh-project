import os
from dotenv import load_dotenv
import google.generativeai as genai

RECORDINGS_DIR = "recordings" # Base directory name for recordings

# --- Configuration Loading ---
def load_config():
    """Load environment variables from .env file and return them."""
    
    # Automatically load environment variables from .env located in the 
    # current working directory (project root) or its parents.
    load_dotenv()
    
    # Get the data directory path *after* loading .env
    adsh_data_dir = os.getenv('ADSH_DATA_DIR')
    if not adsh_data_dir:
        raise EnvironmentError("Required environment variable ADSH_DATA_DIR is not set (should be in .env or exported).")

    # --- Read Environment Variables --- 
    config = {
        "adsh_data_dir": adsh_data_dir, # Add data dir path to config
        "twilio_account_sid": os.getenv("TWILIO_ACCOUNT_SID"),
        "twilio_auth_token": os.getenv("TWILIO_AUTH_TOKEN"),
        "twilio_phone_number": os.getenv("TWILIO_PHONE_NUMBER"),
        "hotline_phone_number": os.getenv("HOTLINE_PHONE_NUMBER"),
        "personal_phone_number": os.getenv("PERSONAL_PHONE_NUMBER"),
        "google_api_key": os.getenv("GOOGLE_API_KEY"),
        "recordings_dir": os.path.join(adsh_data_dir, RECORDINGS_DIR), # Construct recordings dir path using adsh_data_dir
        "log_file": os.path.join(adsh_data_dir, 'logs', 'adsh_log.md'), # Construct log file path using adsh_data_dir
        # NTFY Configuration
        "ntfy_server_url": os.getenv("NTFY_SERVER_URL"),
        "ntfy_topic_logs": os.getenv("NTFY_TOPIC_LOGS"),   # Specific topic for logs
        "ntfy_topic_errors": os.getenv("NTFY_TOPIC_ERRORS"), # Specific topic for errors
        "ntfy_username": os.getenv("NTFY_USERNAME"),
        "ntfy_password": os.getenv("NTFY_PASSWORD"),
    }
    # --- Refined Configuration Validation ---
    required_keys = [
        "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER",
        "HOTLINE_PHONE_NUMBER", "GOOGLE_API_KEY", # Keep PERSONAL_PHONE_NUMBER optional
        "NTFY_SERVER_URL", "NTFY_TOPIC_LOGS", "NTFY_TOPIC_ERRORS",
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
            f"Please check your .env file at the project root."
        )
    # ------------------------------------

    # --- Ensure Required Directories Exist (Only Recordings now) ---
    # Get paths from the final config dict
    recordings_path = config['recordings_dir']

    try:
        os.makedirs(recordings_path, exist_ok=True)
        print(f"   Ensured directory exists: {recordings_path}")
    except OSError as e:
        # Handle potential permission errors or other OS issues
        print(f"[ERROR] Could not create directories: {e}")
        raise

    # Validate GOOGLE_API_KEY specifically for Gemini setup
    if not config.get("google_api_key"):
        raise ValueError("Missing environment variable: GOOGLE_API_KEY")
    else:
        genai.configure(api_key=config['google_api_key'])

    return config

# --- Optional: Load INI config (if needed in future) ---
