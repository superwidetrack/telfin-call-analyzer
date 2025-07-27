# Automated Call Analysis System for "29ROZ"

## Overview
Python application that automates the process of analyzing sales calls from a flower shop.

## Features
- **Fetch Calls**: Connect to Telphin API to get recent calls
- **Download Recordings**: Download audio recording files
- **Transcribe Audio**: Use Yandex SpeechKit API for text transcription
- **Analyze Conversation**: Use OpenAI GPT-4 for quality analysis
- **Send Report**: Format analysis and send to Telegram chat

## Setup

### 1. Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.template .env
# Edit .env file with your API credentials
```

### 3. Required API Credentials
- **Telphin API**: Login and password for call data access
- **Yandex SpeechKit**: API key for speech-to-text transcription
- **OpenAI API**: API key for GPT-4 analysis
- **Telegram Bot**: Bot token and chat ID for notifications

## Usage

### Test Telphin Integration
```bash
python main.py
```

## Project Structure
```
call_analyzer/
├── main.py              # Main application script
├── requirements.txt     # Python dependencies
├── .env.template       # Environment variables template
├── .env               # Your API credentials (create from template)
└── README.md          # This file
```

## API Endpoints

### Telphin API
- **Authentication**: `POST https://apiproxy.telphin.ru/api/ver1.0/auth/`
- **Get Calls**: `GET https://apiproxy.telphin.ru/api/ver1.0/client/@me/calls/`

## Development Status

### ✅ Completed
- [x] Project setup with virtual environment
- [x] Modular code structure
- [x] Telphin API authentication function
- [x] Telphin API calls retrieval function
- [x] Environment variables configuration

### 🔄 In Progress
- [ ] Test Telphin API integration (waiting for credentials)

### 📋 Planned
- [ ] Audio recording download functionality
- [ ] Yandex SpeechKit integration
- [ ] OpenAI GPT-4 analysis integration
- [ ] Telegram notifications
- [ ] Error handling and logging improvements
- [ ] Configuration for call filtering and analysis criteria
