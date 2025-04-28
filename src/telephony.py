import os
import time
import datetime
import requests
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from requests.exceptions import RequestException

# --- Twilio Functions ---
def generate_twiml_for_record():
    """Generate TwiML to immediately record the call."""
    twiml = '<Response><Record/></Response>'
    return twiml

def initiate_call(client, twilio_number, target_number, twiml):
    """Initiate the outbound call using Twilio."""
    try:
        print("   [Telephony] Initiating call...")
        call = client.calls.create(
            twiml=twiml,
            to=target_number,
            from_=twilio_number
        )
        return call.sid
    except TwilioRestException as e:
        print(f"   [ERROR][Telephony] Failed to initiate call: {e.status} {e.method} {e.uri} - {e.msg}")
        return None

def get_recording_uri(client, call_sid):
    """Wait for call completion and retrieve the recording URI."""
    print(f"   [Telephony] Waiting for call {call_sid} to complete...")
    wait_time = 0
    max_wait_time = 180 # Max wait 3 minutes
    poll_interval = 5   # Check every 5 seconds

    while wait_time < max_wait_time:
        try:
            call = client.calls(call_sid).fetch()
            print(f"   Call status: {call.status}")
            if call.status in ['completed', 'failed', 'no-answer', 'canceled']:
                break
        except TwilioRestException as e:
            print(f"   [ERROR][Telephony] Failed to fetch call status: {e.status} {e.method} {e.uri} - {e.msg}")
            time.sleep(poll_interval)
            wait_time += poll_interval
            continue

        time.sleep(poll_interval)
        wait_time += poll_interval
    else:
        raise TimeoutError(f"Call {call_sid} did not complete within {max_wait_time} seconds.")

    if call.status != 'completed':
        raise RuntimeError(f"Call {call_sid} ended with status: {call.status}")

    print("   Call completed. Fetching recordings...")
    try:
        recordings = client.recordings.list(call_sid=call_sid, limit=1)
        if recordings:
            recording = recordings[0]
            print(f"   Found recording SID: {recording.sid}")
            recording_media_uri = f"https://api.twilio.com{recording.uri.replace('.json', '.wav')}"
            return recording_media_uri, recording.sid
        else:
            raise FileNotFoundError(f"No recordings found for call SID: {call_sid}")
    except TwilioRestException as e:
        print(f"   [ERROR][Telephony] Failed to list recordings: {e.status} {e.method} {e.uri} - {e.msg}")
        return None

def download_recording(client, call_sid, recording_uri, recordings_dir):
    """Download the recording audio file from Twilio and save it permanently."""
    print(f"   [Telephony] Downloading recording for Call SID: {call_sid}...")
    if not recording_uri.endswith('.wav'):
        recording_uri += '.wav'

    # Ensure the recordings directory exists (should be handled by config_loader, but defensive check)
    if not os.path.exists(recordings_dir):
        os.makedirs(recordings_dir)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    local_filename = f"recording_{timestamp}.wav"
    local_filepath = os.path.join(recordings_dir, local_filename)

    try:
        print("   Waiting 10 seconds for recording media to finalize...")
        time.sleep(10)

        response = requests.get(
            recording_uri,
            auth=(client.username, client.password),
            stream=True 
        )
        response.raise_for_status()  

        with open(local_filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"   Recording saved successfully to: {local_filepath}")
        return local_filepath 
    except RequestException as e:
        print(f"   [ERROR][Telephony] Error downloading recording: {e}")
        if os.path.exists(local_filepath):
            os.remove(local_filepath)
        return None
    except Exception as e:
        print(f"   An unexpected error occurred during download: {e}")
        if os.path.exists(local_filepath):
            os.remove(local_filepath)
        raise

def delete_recording(client, recording_sid):
    """Delete the recording from Twilio."""
    try:
        deleted = client.recordings(recording_sid).delete()
        if deleted:
            print(f"   Successfully deleted recording SID: {recording_sid}")
            return True
        else:
            print(f"   Failed to delete recording SID: {recording_sid} (API returned False)")
            return False
    except TwilioRestException as e:
        print(f"   [ERROR][Telephony] Error deleting recording SID {recording_sid}: {e.status} {e.method} {e.uri} - {e.msg}")
        return False
