import os
import datetime

def append_log_entry(log_file, color, summary):
    """Append the analysis result to the Markdown log file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"\n---\n**Timestamp:** {timestamp}\n**Color:** {color}\n**Summary:**\n```\n{summary}\n```\n"
    try:
        with open(log_file, 'a') as f:
            f.write(log_entry)
        print(f"   Log entry appended to {log_file}")
    except IOError as e:
        print(f"Error appending to log file {log_file}: {e}")
