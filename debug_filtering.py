#!/usr/bin/env python3
"""
Debug script to test call filtering logic with different time windows.
This will help identify why 30 incoming calls with duration > 0 aren't being processed in 1-hour window.
"""

import os
import sys
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import authenticate_telfin, get_recent_calls, get_call_cdr, MOSCOW_TZ

load_dotenv()

def has_recording(hostname, token, call_uuid):
    """Check if a call has an audio recording available."""
    try:
        cdr_record = get_call_cdr(hostname, token, call_uuid)
        if cdr_record and cdr_record.get('record_file_size', 0) > 0:
            return True, cdr_record.get('record_file_size', 0)
        return False, 0
    except Exception as e:
        print(f"Error checking recording for {call_uuid}: {e}")
        return False, 0

def debug_call_filtering():
    """Debug the call filtering logic with different time windows."""
    print("=== DEBUG: Call Filtering Analysis ===")
    
    hostname = os.environ.get("TELFIN_HOSTNAME")
    login = os.environ.get("TELFIN_LOGIN") 
    password = os.environ.get("TELFIN_PASSWORD")
    
    if not all([hostname, login, password]):
        print("Error: Missing Telphin credentials")
        return
    
    print(f"Authenticating with Telphin API at {hostname}...")
    token = authenticate_telfin(hostname, login, password)
    
    if not token:
        print("Authentication failed")
        return
    
    time_windows = [1, 6, 24, 48]
    
    for hours in time_windows:
        print(f"\n{'='*50}")
        print(f"TESTING {hours}-HOUR WINDOW")
        print(f"{'='*50}")
        
        os.environ["TIME_WINDOW_HOURS"] = str(hours)
        
        calls = get_recent_calls(hostname, token)
        
        if calls is None:
            print(f"Failed to retrieve calls for {hours}-hour window")
            continue
        
        print(f"Total calls retrieved: {len(calls)}")
        
        incoming_calls = []
        calls_with_duration = []
        calls_with_recordings = []
        
        for call in calls:
            flow = call.get('flow', '')
            duration = call.get('duration', 0)
            bridged_duration = call.get('bridged_duration', 0)
            call_uuid = call.get('call_uuid')
            
            if flow == 'in':
                incoming_calls.append(call)
                
            if duration > 0 or bridged_duration > 0:
                calls_with_duration.append(call)
                
            if call_uuid and flow == 'in':
                has_rec, rec_size = has_recording(hostname, token, call_uuid)
                if has_rec:
                    calls_with_recordings.append(call)
        
        current_filtered = [call for call in calls 
                          if call.get('flow') == 'in' and 
                          (call.get('duration', 0) > 0 or call.get('bridged_duration', 0) > 0)]
        
        print(f"Incoming calls: {len(incoming_calls)}")
        print(f"Calls with duration > 0: {len(calls_with_duration)}")
        print(f"Current filter (incoming + duration): {len(current_filtered)}")
        print(f"Incoming calls with recordings: {len(calls_with_recordings)}")
        
        if calls_with_recordings:
            print(f"\nDETAILS OF {len(calls_with_recordings)} INCOMING CALLS WITH RECORDINGS:")
            for i, call in enumerate(calls_with_recordings[:5]):
                call_uuid = call.get('call_uuid')
                duration = call.get('duration', 0)
                bridged_duration = call.get('bridged_duration', 0)
                result = call.get('result', 'N/A')
                start_time = call.get('start_time_gmt', 'N/A')
                
                has_rec, rec_size = has_recording(hostname, token, call_uuid)
                
                print(f"  {i+1}. UUID: {call_uuid}")
                print(f"     Time: {start_time}")
                print(f"     Duration: {duration}s, Bridged: {bridged_duration}s")
                print(f"     Result: {result}")
                print(f"     Recording: {rec_size} bytes")
                print()
        else:
            print("No incoming calls with recordings found!")
            
        print(f"\nSAMPLE OF ALL {len(calls)} CALLS:")
        for i, call in enumerate(calls[:3]):
            flow = call.get('flow', 'N/A')
            duration = call.get('duration', 0)
            result = call.get('result', 'N/A')
            start_time = call.get('start_time_gmt', 'N/A')
            print(f"  {i+1}. Flow: {flow}, Duration: {duration}s, Result: {result}, Time: {start_time}")

if __name__ == "__main__":
    debug_call_filtering()
