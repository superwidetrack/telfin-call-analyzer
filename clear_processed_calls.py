#!/usr/bin/env python3
"""
Script to clear the processed_calls.txt file when deploying new filtering logic.
This ensures the system will reanalyze calls with the new improved filtering rules.
"""

import os

def clear_processed_calls():
    """Clear the processed calls file."""
    processed_calls_file = "processed_calls.txt"
    
    if os.path.exists(processed_calls_file):
        with open(processed_calls_file, 'w') as f:
            f.write("")
        print(f"✅ Cleared {processed_calls_file}")
    else:
        print(f"ℹ️ {processed_calls_file} does not exist, nothing to clear")

if __name__ == "__main__":
    clear_processed_calls()
