import google.generativeai as genai
import json
import time
import os
from google.api_core import exceptions as google_exceptions

# --- Gemini Analysis ---
def analyze_audio_with_gemini(audio_file_path):
    """
    Analyzes the audio file using Google Gemini 2.0 Flash, extracting color, date, and summary.

    Args:
        audio_file_path (str): The path to the audio file.

    Returns:
        tuple: A tuple containing (color, date, summary).
               Returns ('error_parsing', 'N/A', 'Error parsing LLM response') on JSON parsing failure.
               Returns ('error_uploading', 'N/A', 'Error uploading file to API') on upload failure.
               Returns ('error_api', 'N/A', 'API Error message') on API call failure.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY environment variable not set.")

    print(f"   Uploading audio file: {audio_file_path}...")
    
    # Configure the generative model 
    # Ensure genai.configure(api_key=...) has been called previously (e.g., in config_loader)
    model = genai.GenerativeModel('models/gemini-2.0-flash')
    
    audio_file = None
    # Retry mechanism for file upload
    max_retries = 3
    retry_delay = 5 # seconds
    for attempt in range(max_retries):
        try:
            audio_file = genai.upload_file(path=audio_file_path)
            print(f"   Successfully uploaded file: {audio_file.display_name}")
            # Wait until the file is ACTIVE
            while audio_file.state.name == "PROCESSING":
                print('   Waiting for file processing...')
                time.sleep(5)
                audio_file = genai.get_file(audio_file.name)
            
            if audio_file.state.name == "FAILED":
                raise ValueError(f"Audio file processing failed: {audio_file.state.name}")
            elif audio_file.state.name != "ACTIVE":
                 raise ValueError(f"Audio file is not active, state: {audio_file.state.name}")
            break # Exit loop on success
        except google_exceptions.GoogleAPIError as gae:
            print(f"   [ERROR][AudioAnalyzer] Google API error during upload attempt {attempt + 1}: {gae}")
            # Fall through to retry logic
        except Exception as e:
            print(f"   Upload attempt {attempt + 1} failed: {e}")
            if attempt + 1 == max_retries:
                print("   Max upload retries reached. Failing analysis.")
                return ('error_uploading', 'N/A', f'Max upload retries reached: {e}') # Return specific error tuple
            print(f"   Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

    if not audio_file:
        # This case is now handled by the return in the retry loop
        return ('error_uploading', 'N/A', 'Failed to upload audio file after multiple retries.')

    print("   Analyzing audio with Gemini 2.0 Flash...")
    # Make the request to the model
    prompt = """
**TASK**: Extract the color name, date, and summary from an drug screening hotline audio recording.
- Aside from the opening greeting and closing message, the recording typically contains drug screen scheduling information that designates a date and a color.
    - For example "The color of Monday, April 6th is blue."
    - A date and color name are usually stated clearly.
- Identify the single color name and the date mentioned in the recording, after the opening greeting.
- Respond ONLY with a JSON object containing THREE keys:
  - 'color' (the identified color name as a lowercase string)
  - 'date' (the date mentioned, e.g., 'Wednesday, April 23rd', 'April 24th', or 'N/A' if not mentioned)
  - 'summary' (a brief text summary of the main recording content. Omit the opening greeting and closing message about the voice mailbox).
- If no color is clearly identifiable, the 'color' value should be 'unknown'.
- If no date is clearly identifiable, the 'date' value should be 'N/A'.
- Example format:

```json
{"color": "blue", "date": "Wednesday, April 23rd", "summary": "Drug screening for Blue announced for Wednesday, April 23rd."}
```
"""
    try:
        response = model.generate_content([prompt, audio_file], request_options={'timeout': 120})
        
        # Improved parsing with error handling
        try:
            # Extract the JSON part carefully, handling potential markdown backticks
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip() # Strip again after removing backticks
            
            result_json = json.loads(response_text)
            color = result_json.get('color', 'error_parsing').lower()
            # Get the date, default to 'N/A' if missing
            date_found = result_json.get("date", "N/A")
            summary = result_json.get('summary', 'Could not parse summary from response.')
            print(f"   Analysis complete. Color: {color}, Date: {date_found}")
            return color, date_found, summary
        except (json.JSONDecodeError, AttributeError, KeyError, TypeError) as e:
            print(f"   Error parsing Gemini response: {e}")
            print(f"   Raw response text: {response.text}")
            # Try a simple extraction if JSON fails (less reliable)
            raw_text = response.text.lower()
            found_color = 'unknown'
            # Add more colors if needed
            possible_colors = ['red', 'blue', 'green', 'yellow', 'orange', 'purple', 'brown', 'black', 'white', 'gray'] 
            for c in possible_colors:
                if c in raw_text:
                    found_color = c
                    print(f"   Found color '{c}' via simple text search as fallback.")
                    break # Take the first match
            return found_color, 'N/A', f"Error parsing JSON, raw response: {response.text}"

    except google_exceptions.GoogleAPIError as gae:
        print(f"   [ERROR][AudioAnalyzer] Google API error during analysis request: {gae}")
        return ('error_api', 'N/A', f'Google API Error: {gae}') # Return specific error tuple
    except Exception as e:
        print(f"   Error during Gemini analysis request: {e}")
        return ('error_unknown', 'N/A', f'Unknown analysis error: {e}') # Return generic error tuple

    finally:
        # Clean up the uploaded file from Google Cloud storage
        if audio_file:
            try:
                print(f"   Attempting to delete uploaded file: {audio_file.name}")
                genai.delete_file(audio_file.name)
                print(f"   Successfully deleted uploaded file.")
            except google_exceptions.GoogleAPIError as gae:
                # Log error but don't fail the whole process just for cleanup
                print(f"   [WARNING][AudioAnalyzer] Google API error deleting uploaded file {audio_file.name}: {gae}")
            except Exception as e:
                # Log error but don't fail the whole process just for cleanup
                print(f"   Warning: Failed to delete uploaded file {audio_file.name}: {e}")
