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

def download_recording():
    """
    Placeholder for download_recording function.
    To be implemented in future iterations.
    """
    pass

def transcribe_with_yandex():
    """
    Placeholder for transcribe_with_yandex function.
    To be implemented in future iterations.
    """
    pass

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
    Main function to test Telphin API integration.
    """
    print("=== Automated Call Analysis System for 29ROZ ===")
    print("Testing Telphin API integration...")
    
    hostname = os.getenv("TELFIN_HOSTNAME")
    login = os.getenv("TELFIN_LOGIN")
    password = os.getenv("TELFIN_PASSWORD")
    
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
    
    print("Telphin API integration test completed successfully!")

if __name__ == "__main__":
    main()
