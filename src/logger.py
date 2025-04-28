import datetime

def append_log_entry(log_file, color, summary):
    """Append the analysis result to the Markdown log file."""
    # Get current time in UTC and format it
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    log_entry = f"\n---\n**Timestamp:** {timestamp}\n**Color:** {color}\n**Summary:**\n```\n{summary}\n```\n"
    try:
        with open(log_file, 'a') as f:
            f.write(log_entry)
        print(f"   Log entry appended to {log_file}")
    except IOError as e:
        print(f"Error appending to log file {log_file}: {e}")
