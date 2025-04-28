import datetime
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from google.api_core import exceptions as google_exceptions
import requests
import os

from .config_loader import load_config
from .telephony import (
    generate_twiml_for_record, 
    initiate_call, 
    get_recording_uri, 
    download_recording, 
    delete_recording
)
from .audio_analyzer import analyze_audio_with_gemini
from .logger import append_log_entry
from .notifier import send_ntfy_notification

def main():
    """Main execution function to orchestrate the call and analysis process."""
    start_time_iso = datetime.datetime.now().isoformat() # Capture start time
    print(f"[{start_time_iso}] Script started.")
    config = None
    call_sid = None
    recording_sid = None
    permanent_audio_path = None

    try:
        # 1. Load Configuration
        config = load_config()

        # Ensure recordings directory exists
        recordings_dir = config['recordings_dir'] # Use lowercase key

        # 2. Initialize Twilio Client
        twilio_client = Client(config['twilio_account_sid'], config['twilio_auth_token'])
        print("   Twilio client initialized.")

        # 3. Generate TwiML
        twiml = generate_twiml_for_record()
        print("   Generated TwiML for recording.")

        # 4. Initiate Call
        print(f"   Initiating call to {config['hotline_phone_number']}...")
        call_sid = initiate_call(
            twilio_client, 
            config['twilio_phone_number'], 
            config['hotline_phone_number'], 
            twiml
        )
        if not call_sid:
            raise RuntimeError("Failed to initiate Twilio call. Check logs and Twilio credentials.")
        print(f"   Call initiated successfully with SID: {call_sid}")

        # 5. Get Recording URI (includes waiting for call completion)
        recording_uri, recording_sid = get_recording_uri(twilio_client, call_sid)
        print(f"   Found recording SID: {recording_sid}") # Log only the SID

        # 6. Download Recording
        permanent_audio_path = download_recording(
            twilio_client, 
            call_sid, 
            recording_uri, 
            config['recordings_dir'] # Pass recordings directory from config
        )
        print(f"   Recording downloaded to: {permanent_audio_path}")

        # 7. Analyze Audio
        if permanent_audio_path:
            # Capture timestamp *before* sending notification
            analysis_complete_time = datetime.datetime.now()
            analysis_complete_ts_str = analysis_complete_time.strftime("%Y-%m-%d %H:%M:%S") # Formatted timestamp

            # Call updated analyzer function
            color, date_found, summary = analyze_audio_with_gemini(permanent_audio_path)
            print(f"   Analysis result - Color: {color}, Date: {date_found}")

            # 8. Log Result to file
            # Consider adding date_found to log entry if useful
            append_log_entry(config['log_file'], color, summary) # Currently logs color and summary

            # --- Prepare and Send Notifications ---
            # Common elements
            ntfy_args = {
                "server_url": config["ntfy_server_url"],
                "username": config["ntfy_username"],
                "password": config["ntfy_password"],
            }

            # Send Log Notification (lower priority) - New Format
            log_title = f"{color.capitalize()}, {date_found if date_found != 'N/A' else 'Date Unknown'}" # Simplified Title
            log_message = f"Summary: {summary}" # Simplified Message
            send_ntfy_notification(
                **ntfy_args,
                topic=config["ntfy_topic_logs"], # Use logs topic
                title=log_title,
                message=log_message,
                priority=3 # Lower priority for logs
            )

            # Send Alert Notification if target color found (high priority) - New Format
            if color == config['target_color']:
                alert_title = f"{color.capitalize()}, {date_found if date_found != 'N/A' else 'Date Unknown'}" # Simplified Title (consistent with logs)
                # Message body can be similar or more specific
                alert_message = f"Summary: {summary}" # Simplified Message
                print(f"   [Main] Target color '{color}' found, sending alert...")
                send_ntfy_notification(
                    **ntfy_args,
                    topic=config["ntfy_topic_alerts"], # Use alerts topic
                    title=alert_title,
                    message=alert_message,
                    priority=5 # Highest priority for alerts
                )
        else:
            print("   Skipping analysis and logging because audio download failed.")
            # Optionally send error notification here?

    # Specific Exception Handling
    except KeyError as ke:
        # Error loading essential configuration
        error_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_title = "ADSH Config Error"
        error_message = f"Missing essential configuration key: {ke}\nTimestamp: {error_ts}"
        print(f"[CRITICAL][{error_ts}] {error_message}")
        # Cannot reliably send NTFY if config is incomplete, just print
        # Optionally, could try sending NTFY with hardcoded defaults if really needed

    except TwilioRestException as tre:
        # Error interacting with Twilio API
        error_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_title = "ADSH Twilio Error"
        error_message = f"Twilio API Error: {tre.status} {tre.method} {tre.uri}\nMessage: {tre.msg}\nTimestamp: {error_ts}"
        print(f"[ERROR][{error_ts}] {error_message}")
        append_log_entry(config.get('log_file', 'error_log.md'), "error_twilio", str(tre))
        if config.get("ntfy_server_url") and config.get("ntfy_topic_errors"):
             send_ntfy_notification(
                 server_url=config["ntfy_server_url"], topic=config["ntfy_topic_errors"],
                 username=config["ntfy_username"], password=config["ntfy_password"],
                 title=error_title, message=error_message, priority=5
             )

    except google_exceptions.GoogleAPIError as gae:
        # Error interacting with Google Gemini API
        error_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_title = "ADSH Gemini API Error"
        error_message = f"Google API Error: {type(gae).__name__}: {gae}\nTimestamp: {error_ts}"
        print(f"[ERROR][{error_ts}] {error_message}")
        append_log_entry(config.get('log_file', 'error_log.md'), "error_google_api", str(gae))
        if config.get("ntfy_server_url") and config.get("ntfy_topic_errors"):
             send_ntfy_notification(
                 server_url=config["ntfy_server_url"], topic=config["ntfy_topic_errors"],
                 username=config["ntfy_username"], password=config["ntfy_password"],
                 title=error_title, message=error_message, priority=5
             )

    except ValueError as ve:
        # Typically from load_config if validation fails
        error_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_title = "ADSH Value Error"
        error_message = f"Value Error (likely config related): {ve}\nTimestamp: {error_ts}"
        print(f"[ERROR][{error_ts}] {error_message}")
        # Config might be partially loaded, attempt logging/NTFY
        if config:
            append_log_entry(config.get('log_file', 'error_log.md'), "error_value", str(ve))
            if config.get("ntfy_server_url") and config.get("ntfy_topic_errors"):
                 send_ntfy_notification(
                     server_url=config["ntfy_server_url"], topic=config["ntfy_topic_errors"],
                     username=config["ntfy_username"], password=config["ntfy_password"],
                     title=error_title, message=error_message, priority=5
                 )

    except FileNotFoundError as fnfe:
        error_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_title = "ADSH File Error"
        error_message = f"File Not Found Error: {fnfe}\nTimestamp: {error_ts}"
        print(f"[ERROR][{error_ts}] {error_message}")
        if config:
            append_log_entry(config.get('log_file', 'error_log.md'), "error_file", str(fnfe))
            if config.get("ntfy_server_url") and config.get("ntfy_topic_errors"):
                 send_ntfy_notification(
                     server_url=config["ntfy_server_url"], topic=config["ntfy_topic_errors"],
                     username=config["ntfy_username"], password=config["ntfy_password"],
                     title=error_title, message=error_message, priority=5
                 )

    except requests.exceptions.RequestException as re:
        error_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_title = "ADSH Network Error"
        error_message = f"Network Request Error: {type(re).__name__}: {re}\nTimestamp: {error_ts}"
        print(f"[ERROR][{error_ts}] {error_message}")
        if config:
            append_log_entry(config.get('log_file', 'error_log.md'), "error_network", str(re))
            if config.get("ntfy_server_url") and config.get("ntfy_topic_errors"):
                 send_ntfy_notification(
                     server_url=config["ntfy_server_url"], topic=config["ntfy_topic_errors"],
                     username=config["ntfy_username"], password=config["ntfy_password"],
                     title=error_title, message=error_message, priority=5
                 )

    except TimeoutError as te:
        # Specific handling for call polling timeout
        error_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_title = "ADSH Critical Error: Call Timeout"
        # Keep existing specific message for timeout
        error_message = f"Call polling timed out for SID {call_sid if 'call_sid' in locals() else 'N/A'}.\nTimestamp: {error_ts}"
        print(f"[ERROR][{error_ts}] {error_message}")
        if config: # Check if config exists before logging/notifying
            append_log_entry(config.get('log_file', 'error_log.md'), "error_timeout", str(te))
            # Send error notification for timeout
            if config.get("ntfy_server_url") and config.get("ntfy_topic_errors"):
                send_ntfy_notification(
                    server_url=config["ntfy_server_url"],
                    topic=config["ntfy_topic_errors"], username=config["ntfy_username"],
                    password=config["ntfy_password"], title=error_title,
                    message=error_message, priority=5
                )

    except Exception as e:
        # Generic fallback for any other unexpected errors
        error_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_title = "ADSH Critical Unhandled Error"
        error_message = f"An unexpected error occurred: {type(e).__name__}: {e}\nTimestamp: {error_ts}\nCheck application logs."
        print(f"[CRITICAL][{error_ts}] {error_message}")
        # Send error notification if config was loaded successfully
        if config and config.get("ntfy_server_url") and config.get("ntfy_topic_errors"):
            send_ntfy_notification(
                server_url=config["ntfy_server_url"],
                topic=config["ntfy_topic_errors"], username=config["ntfy_username"],
                password=config["ntfy_password"],
                title=error_title, message=error_message, priority=5
            )

    finally:
        # 9. Clean up Twilio Recording (only if call SID exists)
        if call_sid and recording_uri: # Check if recording_uri was obtained
            # Ensure recording SID exists before attempting deletion
            print(f"   [Main] Attempting to delete Twilio recording {recording_sid}...")
            # Pass the initialized client and the SID
            delete_recording(twilio_client, recording_sid)
        elif call_sid:
            print(f"   [Main] No recording URI obtained for call {call_sid}, skipping recording deletion.")

        finish_time_iso = datetime.datetime.now().isoformat()
        print(f"[{finish_time_iso}] Script finished.")

if __name__ == "__main__":
    main()
