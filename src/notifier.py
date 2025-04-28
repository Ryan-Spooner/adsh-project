import requests
import base64

def send_ntfy_notification(server_url, topic, username, password, title, message, priority=4):
    """Sends a notification to an NTFY server using Basic Authentication.

    Args:
        server_url (str): The base URL of the NTFY server (e.g., 'http://localhost:9090').
        topic (str): The NTFY topic to publish to.
        username (str): The username for Basic Authentication.
        password (str): The password for Basic Authentication.
        title (str): The title of the notification.
        message (str): The main body/message of the notification.
        priority (int, optional): The priority of the message (1-5). Defaults to 4 (high).

    Returns:
        bool: True if the notification was sent successfully, False otherwise.
    """
    if not all([server_url, topic, username, password, title, message]):
        print("[ERROR][Notifier] Missing required arguments for sending notification.")
        return False

    # Construct the full URL
    publish_url = f"{server_url.rstrip('/')}/{topic}"

    # Prepare Basic Authentication header
    auth_string = f"{username}:{password}"
    encoded_auth = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    headers = {
        'Authorization': f'Basic {encoded_auth}',
        'Title': title, # Use the Title header for the notification title
        'Priority': str(priority) # Priority header
        # Content-Type is typically text/plain by default for ntfy messages
    }

    try:
        print(f"   [Notifier] Sending notification to {publish_url}...")
        try:
            response = requests.post(
                publish_url,
                headers=headers,
                data=message.encode('utf-8'), # Send message body as data, encoded
                timeout=10 # Add a timeout
            )

            response.raise_for_status() # Raise an HTTPError for bad status codes (4xx or 5xx)
            
            print(f"   [Notifier] Notification sent successfully (Status: {response.status_code}).")
            return True

        except requests.exceptions.RequestException as e:
            print(f"[ERROR][Notifier] Request failed sending notification to {publish_url}: {e}")
            return False

    except Exception as e:
        print(f"[ERROR][Notifier] An unexpected error occurred: {e}")
        return False
