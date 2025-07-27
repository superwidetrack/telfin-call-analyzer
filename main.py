import os
import requests
from dotenv import load_dotenv

load_dotenv()

def authenticate_telfin(hostname, login, password):
    """
    Authenticate with Telphin API and get bearer token.
    
    Args:
        hostname (str): Telphin hostname
        login (str): Telphin login
        password (str): Telphin password
    
    Returns:
        str: Bearer token if successful, None if failed
    """
    auth_url = f"https://{hostname}:443/oauth/token"
    
    auth_data = {
        "grant_type": "client_credentials",
        "application_id": login,
        "application_secret": password
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        response = requests.post(auth_url, data=auth_data, headers=headers)
        response.raise_for_status()
        
        auth_result = response.json()
        token = auth_result.get("access_token")
        
        if token:
            print(f"Authentication successful. Token received.")
            return token
        else:
            print("Authentication failed: No token in response")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Authentication error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during authentication: {e}")
        return None

def get_recent_calls(hostname, token, client_id="@me"):
    """
    Get list of recent calls from Telphin API.
    
    Args:
        hostname (str): Telphin hostname
        token (str): Bearer token from authentication
        client_id (str): Client ID, defaults to "@me"
    
    Returns:
        list: List of calls if successful, None if failed
    """
    from datetime import datetime, timedelta
    
    end_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    start_datetime = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    
    calls_url = f"https://{hostname}/api/ver1.0/client/{client_id}/calls/"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    params = {
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "per_page": 100
    }
    
    try:
        response = requests.get(calls_url, headers=headers, params=params)
        response.raise_for_status()
        
        calls_data = response.json()
        
        if isinstance(calls_data, dict) and 'calls' in calls_data:
            calls_list = calls_data['calls']
            print(f"Successfully retrieved {len(calls_list)} calls")
            return calls_list
        elif isinstance(calls_data, list):
            print(f"Successfully retrieved {len(calls_data)} calls")
            return calls_data
        elif isinstance(calls_data, dict) and 'results' in calls_data:
            calls_list = calls_data['results']
            print(f"Successfully retrieved {len(calls_list)} calls")
            return calls_list
        else:
            print("Unexpected response format for calls data")
            print(f"Debug: Response keys = {list(calls_data.keys()) if isinstance(calls_data, dict) else 'Not a dict'}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving calls: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error retrieving calls: {e}")
        return None

def get_call_cdr(hostname, token, call_uuid):
    """
    Get call detail record (CDR) for a specific call to find recording information.
    
    Args:
        hostname (str): Telphin hostname
        token (str): Bearer token from authentication
        call_uuid (str): UUID of the call to get CDR for
    
    Returns:
        dict: CDR data if successful, None if failed
    """
    from datetime import datetime, timedelta
    
    end_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    start_datetime = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    
    cdr_url = f"https://{hostname}/api/ver1.0/client/@me/cdr/"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    params = {
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "per_page": 1000
    }
    
    try:
        print(f"Getting CDR data to find recording info for call {call_uuid}...")
        response = requests.get(cdr_url, headers=headers, params=params)
        response.raise_for_status()
        
        cdr_data = response.json()
        
        if isinstance(cdr_data, dict) and 'cdr' in cdr_data:
            cdr_list = cdr_data['cdr']
            for cdr_record in cdr_list:
                if cdr_record.get('call_uuid') == call_uuid:
                    print(f"Found CDR record for call {call_uuid}")
                    return cdr_record
            print(f"Call {call_uuid} not found in CDR data")
            return None
        else:
            print("Unexpected CDR response format")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error getting CDR for call {call_uuid}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error getting CDR: {e}")
        return None

def download_recording(hostname, token, call_uuid):
    """
    Download audio recording for a specific call from Telphin API.
    First gets CDR to find recording info, then downloads from storage_url if available.
    
    Args:
        hostname (str): Telphin hostname
        token (str): Bearer token from authentication
        call_uuid (str): UUID of the call to download recording for
    
    Returns:
        bytes: Binary audio content if successful, None if failed
    """
    cdr_record = get_call_cdr(hostname, token, call_uuid)
    
    if not cdr_record:
        print(f"Could not get CDR for call {call_uuid}")
        return None
    
    record_file_size = cdr_record.get('record_file_size', 0)
    storage_url = cdr_record.get('storage_url')
    record_uuid = cdr_record.get('record_uuid')
    
    print(f"CDR info - File size: {record_file_size}, Storage URL: {storage_url}, Record UUID: {record_uuid}")
    
    if record_file_size == 0:
        print(f"No recording available for call {call_uuid} (file size is 0)")
        return None
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    if storage_url:
        try:
            print(f"Trying to download from storage_url: {storage_url}")
            response = requests.get(storage_url, headers=headers)
            if response.status_code == 200:
                print(f"Successfully downloaded recording from storage_url ({len(response.content)} bytes)")
                return response.content
            else:
                print(f"Storage URL failed with status {response.status_code}")
        except Exception as e:
            print(f"Error downloading from storage_url: {e}")
    
    if record_uuid:
        try:
            recording_url = f"https://{hostname}/api/ver1.0/client/@me/record/{record_uuid}/"
            print(f"Trying to download using record_uuid: {recording_url}")
            response = requests.get(recording_url, headers=headers)
            if response.status_code == 200:
                print(f"Successfully downloaded recording using record_uuid ({len(response.content)} bytes)")
                return response.content
            else:
                print(f"Record UUID method failed with status {response.status_code}")
        except Exception as e:
            print(f"Error downloading using record_uuid: {e}")
    
    try:
        recording_url = f"https://{hostname}/api/ver1.0/client/@me/record/{call_uuid}/"
        print(f"Trying original method with call_uuid: {recording_url}")
        response = requests.get(recording_url, headers=headers)
        
        if response.status_code == 404:
            print(f"No recording found for call {call_uuid} using original method")
            return None
        elif response.status_code == 200:
            print(f"Successfully downloaded recording using original method ({len(response.content)} bytes)")
            return response.content
        else:
            response.raise_for_status()
            
    except requests.exceptions.RequestException as e:
        print(f"Error downloading recording for call {call_uuid}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error downloading recording: {e}")
        return None

def transcribe_with_yandex(api_key, audio_data):
    """
    Transcribe audio data using Yandex SpeechKit API.
    
    Args:
        api_key (str): Yandex SpeechKit API key
        audio_data (bytes): Binary audio content to transcribe
    
    Returns:
        str: Transcribed text if successful, None if failed
    """
    if not api_key or api_key == "your_yandex_api_key":
        print("Error: YANDEX_API_KEY not configured")
        return None
        
    if not audio_data:
        print("Error: No audio data provided")
        return None
    
    if len(audio_data) > 1048576:
        print(f"Error: Audio file too large ({len(audio_data)} bytes). Maximum size is 1 MB.")
        return None
    
    if audio_data.startswith(b'ID3') or audio_data[4:8] == b'ftyp':
        print("Detected MP3 format from Telphin. Converting to OGG Opus for Yandex SpeechKit...")
        
        import tempfile
        import subprocess
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as mp3_file:
                mp3_file.write(audio_data)
                mp3_path = mp3_file.name
            
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as ogg_file:
                ogg_path = ogg_file.name
            
            result = subprocess.run([
                'ffmpeg', '-i', mp3_path, '-c:a', 'libopus', '-b:a', '64k', 
                '-vn', '-f', 'ogg', ogg_path, '-y'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                with open(ogg_path, 'rb') as f:
                    audio_data = f.read()
                print(f"Successfully converted MP3 to OGG Opus ({len(audio_data)} bytes)")
            else:
                print(f"FFmpeg conversion failed: {result.stderr}")
                return None
                
            import os
            os.unlink(mp3_path)
            os.unlink(ogg_path)
            
        except Exception as e:
            print(f"Error during audio conversion: {e}")
            return None
    
    transcription_url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
    
    headers = {
        "Authorization": f"Api-Key {api_key}",
        "Content-Type": "application/octet-stream"
    }
    
    params = {
        "lang": "ru-RU",
        "format": "oggopus",
        "topic": "general"
    }
    
    try:
        print(f"Sending {len(audio_data)} bytes to Yandex SpeechKit for transcription...")
        print(f"Request URL: {transcription_url}")
        print(f"Parameters: {params}")
        
        response = requests.post(
            transcription_url, 
            headers=headers, 
            params=params, 
            data=audio_data
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"Response content: {response.text}")
            response.raise_for_status()
        
        result = response.json()
        print(f"Response JSON: {result}")
        
        if 'result' in result:
            transcribed_text = result['result']
            print(f"Transcription successful: {len(transcribed_text)} characters")
            return transcribed_text
        else:
            print("Unexpected response format from Yandex SpeechKit")
            print(f"Response: {result}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error during transcription: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Error response content: {e.response.text}")
        return None
    except Exception as e:
        print(f"Unexpected error during transcription: {e}")
        return None

def analyze_with_gpt():
    """
    Placeholder for analyze_with_gpt function.
    To be implemented in future iterations.
    """
    pass

def send_telegram_report():
    """
    Placeholder for send_telegram_report function.
    To be implemented in future iterations.
    """
    pass

def main():
    """
    Main function to test Telphin API integration and recording transcription.
    """
    print("=== Automated Call Analysis System for 29ROZ ===")
    print("Testing Telphin API integration and recording transcription...")
    
    hostname = os.getenv("TELFIN_HOSTNAME")
    login = os.getenv("TELFIN_LOGIN")
    password = os.getenv("TELFIN_PASSWORD")
    yandex_api_key = os.getenv("YANDEX_API_KEY")
    
    if not hostname or not login or not password:
        print("Error: TELFIN_HOSTNAME, TELFIN_LOGIN and TELFIN_PASSWORD must be set in .env file")
        print("Please copy .env.template to .env and fill in your credentials")
        return
    
    print(f"\n1. Authenticating with Telphin API at {hostname}...")
    token = authenticate_telfin(hostname, login, password)
    
    if not token:
        print("Authentication failed. Cannot proceed.")
        return
    
    print("\n2. Retrieving recent calls...")
    calls = get_recent_calls(hostname, token)
    
    if calls is None:
        print("Failed to retrieve calls.")
        return
    
    print(f"\n3. Results:")
    print(f"Total calls retrieved: {len(calls)}")
    
    if calls:
        print("\nFirst few calls:")
        for i, call in enumerate(calls[:3]):
            print(f"Call {i+1}:")
            print(f"  Call UUID: {call.get('call_uuid', 'N/A')}")
            print(f"  Start Time: {call.get('start_time_gmt', 'N/A')}")
            print(f"  Duration: {call.get('duration', 'N/A')}")
            print(f"  From: {call.get('from_username', 'N/A')}")
            print(f"  To: {call.get('to_username', 'N/A')}")
            print(f"  Flow: {call.get('flow', 'N/A')}")
            print(f"  Result: {call.get('result', 'N/A')}")
            print()
        
        if yandex_api_key and yandex_api_key != "your_yandex_api_key":
            print(f"\n4. Testing recording download and transcription...")
            
            recording_found = False
            max_attempts = min(50, len(calls))  # Try up to 50 calls or all available calls
            
            for i in range(max_attempts):
                call = calls[i]
                call_uuid = call.get('call_uuid')
                
                if not call_uuid:
                    continue
                    
                print(f"\nAttempt {i+1}: Processing call {call_uuid}")
                print(f"  Call details: {call.get('start_time_gmt')} | {call.get('duration')}s | {call.get('flow')} | {call.get('result')}")
                
                audio_data = download_recording(hostname, token, call_uuid)
                
                if audio_data:
                    recording_found = True
                    print(f"✅ Found recording! Proceeding with transcription...")
                    
                    # Transcribe with Yandex SpeechKit
                    transcribed_text = transcribe_with_yandex(yandex_api_key, audio_data)
                    
                    if transcribed_text:
                        print(f"\n5. Transcription Result:")
                        print("=" * 50)
                        print(transcribed_text)
                        print("=" * 50)
                        print("Recording download and transcription test completed successfully!")
                        break
                    else:
                        print("❌ Transcription failed, trying next call...")
                        continue
                else:
                    print(f"❌ No recording available for this call")
                    continue
            
            if not recording_found:
                print(f"\n❌ No recordings found in the first {max_attempts} calls.")
                print("This might be normal - not all calls have recordings available.")
        else:
            print("\n4. Skipping recording transcription test (YANDEX_API_KEY not configured)")
    
    print("\nTelphin API integration test completed successfully!")

if __name__ == "__main__":
    main()
