import os
import requests
import openai
import asyncio
import json
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

PROCESSED_CALLS_FILE = "processed_calls.json"

def load_processed_calls():
    """
    Load the list of already processed call IDs from JSON file.
    
    Returns:
        set: Set of processed call IDs
    """
    try:
        if os.path.exists(PROCESSED_CALLS_FILE):
            with open(PROCESSED_CALLS_FILE, 'r') as f:
                data = json.load(f)
                return set(data.get('processed_calls', []))
        return set()
    except Exception as e:
        print(f"Error loading processed calls: {e}")
        return set()

def save_processed_call(call_id):
    """
    Add a call ID to the processed calls file.
    
    Args:
        call_id (str): Call ID to mark as processed
    """
    try:
        processed_calls = load_processed_calls()
        processed_calls.add(call_id)
        
        from datetime import datetime
        data = {
            'processed_calls': list(processed_calls),
            'last_updated': datetime.now().isoformat()
        }
        
        with open(PROCESSED_CALLS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"✅ Marked call {call_id} as processed")
    except Exception as e:
        print(f"Error saving processed call: {e}")

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
    start_datetime = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    
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
    start_datetime = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    
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

def analyze_with_gpt(transcript):
    """
    Analyze call transcript using OpenAI GPT-4 for quality assessment.
    
    Args:
        transcript (str): Transcribed text from the call
    
    Returns:
        str: Structured analysis report if successful, None if failed
    """
    openai_api_key = os.environ.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key or openai_api_key == "your_openai_api_key":
        print("Error: OPENAI_API_KEY not configured")
        return None
        
    if not transcript:
        print("Error: No transcript provided for analysis")
        return None
    
    client = openai.OpenAI(api_key=openai_api_key)
    
    prompt = f"""Ты — строгий, но справедливый руководитель отдела контроля качества в цветочном магазине "29ROZ".
Твоя задача — проанализировать разговор менеджера с клиентом и дать четкую, структурированную обратную связь.

**Транскрипция разговора:**
---
{transcript}
---

**Проанализируй диалог по следующему чек-листу:**
1.  **Приветствие:** Поздоровался, представился, назвал компанию "29ROZ"?
2.  **Выявление потребности:** Узнал повод (день рождения, свидание), бюджет, предпочтения по цветам/стилю?
3.  **Презентация:** Предложил конкретные варианты букетов? Рассказал о свежести цветов, уникальности композиции?
4.  **Допродажа:** Предложил сопутствующие товары (открытка, ваза, шарики, мягкая игрушка)?
5.  **Оформление заказа:** Четко проговорил и зафиксировал имя, адрес, телефон получателя и время доставки?
6.  **Завершение:** Поблагодарил за заказ, позитивно завершил диалог?

**Сформируй отчет СТРОГО в следующем формате:**

⭐ **Общая оценка:** [поставь оценку от 1 до 10]

✅ **Что было хорошо:**
- [Краткий пункт 1]
- [Краткий пункт 2]

❌ **Зоны роста:**
- [Конкретный пункт, что нужно улучшить]
- [Конкретный пункт, что нужно улучшить]

💡 **Рекомендация:**
- [Один главный совет менеджеру, что изменить в следующем звонке]"""
    
    try:
        print("Sending transcript to OpenAI GPT-4 for analysis...")
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        analysis = response.choices[0].message.content
        print(f"GPT-4 analysis completed: {len(analysis)} characters")
        return analysis
        
    except Exception as e:
        print(f"Error during GPT-4 analysis: {e}")
        return None

async def send_telegram_report(report_text):
    """
    Send analysis report to Telegram chat.
    
    Args:
        report_text (str): Formatted report text to send
    
    Returns:
        bool: True if successful, False if failed
    """
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or bot_token == "your_telegram_bot_token":
        print("Error: TELEGRAM_BOT_TOKEN not configured")
        return False
        
    if not chat_id or chat_id == "your_telegram_chat_id":
        print("Error: TELEGRAM_CHAT_ID not configured")
        return False
        
    if not report_text:
        print("Error: No report text provided")
        return False
    
    try:
        print(f"Sending report to Telegram chat {chat_id}...")
        
        bot = Bot(token=bot_token)
        await bot.send_message(
            chat_id=chat_id,
            text=report_text,
            parse_mode='Markdown'
        )
        
        print("✅ Report sent to Telegram successfully!")
        return True
        
    except Exception as e:
        print(f"Error sending Telegram report: {e}")
        return False

def main():
    """
    Main function for automated call analysis system.
    Processes all available calls and sends analysis reports to Telegram.
    """
    print("=== Automated Call Analysis System for 29ROZ ===")
    print("Starting automated call analysis...")
    
    hostname = os.environ.get("TELFIN_HOSTNAME") or os.getenv("TELFIN_HOSTNAME")
    login = os.environ.get("TELFIN_LOGIN") or os.getenv("TELFIN_LOGIN")
    password = os.environ.get("TELFIN_PASSWORD") or os.getenv("TELFIN_PASSWORD")
    yandex_api_key = os.environ.get("YANDEX_API_KEY") or os.getenv("YANDEX_API_KEY")
    
    if not hostname or not login or not password:
        print("Error: TELFIN_HOSTNAME, TELFIN_LOGIN and TELFIN_PASSWORD must be set as environment variables")
        return
    
    if not yandex_api_key:
        print("Error: YANDEX_API_KEY must be set as environment variable")
        return
    
    print(f"\n1. Authenticating with Telphin API at {hostname}...")
    token = authenticate_telfin(hostname, login, password)
    
    if not token:
        print("Authentication failed. Cannot proceed.")
        return
    
    print("\n2. Loading processed calls history...")
    processed_calls = load_processed_calls()
    print(f"Found {len(processed_calls)} previously processed calls")
    
    print("\n3. Retrieving recent calls...")
    calls = get_recent_calls(hostname, token)
    
    if calls is None:
        print("Failed to retrieve calls.")
        return
    
    new_calls = [call for call in calls if call.get('call_uuid') not in processed_calls]
    
    print(f"Found {len(calls)} total calls, {len(new_calls)} new calls to process")
    
    if not new_calls:
        print("✅ No new calls to process. All recent calls have been analyzed.")
        return
    
    processed_count = 0
    successful_reports = 0
    
    for i, call in enumerate(new_calls):
        call_uuid = call.get('call_uuid')
        
        if not call_uuid:
            continue
            
        print(f"\nProcessing new call {i+1}/{len(new_calls)}: {call_uuid}")
        print(f"  Details: {call.get('start_time_gmt')} | {call.get('duration')}s | {call.get('flow')} | {call.get('result')}")
        
        audio_data = download_recording(hostname, token, call_uuid)
        
        if audio_data:
            processed_count += 1
            print(f"✅ Recording found! Processing...")
            
            # Transcribe with Yandex SpeechKit
            transcribed_text = transcribe_with_yandex(yandex_api_key, audio_data)
            
            if transcribed_text:
                print(f"✅ Transcription completed")
                
                analysis = analyze_with_gpt(transcribed_text)
                
                if analysis:
                    print(f"✅ GPT-4 analysis completed")
                    
                    final_report = f"""📞 **Анализ звонка 29ROZ**

🔍 **Детали звонка:**
- **ID:** `{call_uuid}`
- **Дата:** {call.get('start_time_gmt', 'N/A')}
- **Длительность:** {call.get('duration', 'N/A')} сек
- **Направление:** {call.get('flow', 'N/A')}
- **Результат:** {call.get('result', 'N/A')}

📝 **Транскрипция:**
```
{transcribed_text}
```

{analysis}

---
*Автоматический анализ системы 29ROZ Call Analyzer*"""
                    
                    telegram_success = asyncio.run(send_telegram_report(final_report))
                    
                    if telegram_success:
                        successful_reports += 1
                        save_processed_call(call_uuid)
                        print("✅ Report sent to Telegram successfully!")
                    else:
                        print("❌ Failed to send Telegram report")
                        print("⚠️  Call will be retried next time due to Telegram failure")
                else:
                    print("❌ GPT-4 analysis failed")
            else:
                print("❌ Transcription failed")
        else:
            print(f"❌ No recording available")
            save_processed_call(call_uuid)
    
    print(f"\n=== Analysis Complete ===")
    print(f"Total calls retrieved: {len(calls)}")
    print(f"New calls processed: {len(new_calls)}")
    print(f"Calls with recordings: {processed_count}")
    print(f"Successful reports sent: {successful_reports}")
    print("Call analysis cycle completed.")

if __name__ == "__main__":
    main()
