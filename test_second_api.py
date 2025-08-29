#!/usr/bin/env python3
"""
Test script to check what data the second API is returning and verify the date filtering.
"""

import requests
import json
from datetime import datetime, timedelta

def is_within_60_days(date_string):
    """Check if a date is within the last 60 days from today"""
    if not date_string or date_string == "N/A":
        return False
    
    try:
        # Handle different date formats
        date_formats = [
            "%Y-%m-%d %H:%M:%S",  # Format from second.json: "2024-07-10 13:33:40"
            "%Y-%m-%dT%H:%M:%S",  # Format from test.json: "2025-02-26T00:00:00"
            "%Y-%m-%dT%H:%M:%SZ", # Format with Z suffix: "2025-01-30T11:24:12Z"
            "%Y-%m-%d",           # Just date: "2024-07-10"
        ]
        
        parsed_date = None
        for date_format in date_formats:
            try:
                parsed_date = datetime.strptime(date_string, date_format)
                break
            except ValueError:
                continue
        
        if parsed_date is None:
            return False
        
        # Calculate the date 60 days ago
        sixty_days_ago = datetime.now() - timedelta(days=60)
        
        # Return True if the date is within the last 60 days
        return parsed_date >= sixty_days_ago
        
    except Exception as e:
        return False

def test_second_api():
    """Test what data the second API is actually returning"""
    url = "http://199.5.83.167:8000/picked"
    
    print("=" * 60)
    print("TESTING SECOND API DATA")
    print("=" * 60)
    
    try:
        print(f"Fetching data from: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        api_data = response.json()
        
        print(f"Total items received from API: {len(api_data)}")
        
        # Analyze dates in the raw API response
        date_samples = []
        old_dates = []
        recent_dates = []
        
        for i, item in enumerate(api_data[:100]):  # Check first 100 items
            timestamp = item.get("TimeStamp", "N/A")
            date_samples.append(timestamp)
            
            if is_within_60_days(timestamp):
                recent_dates.append(timestamp)
            else:
                old_dates.append(timestamp)
        
        print(f"\nSample of first 10 timestamps from API:")
        for i, ts in enumerate(date_samples[:10]):
            within_60 = "✅ RECENT" if is_within_60_days(ts) else "❌ OLD"
            print(f"  {i+1}. {ts} - {within_60}")
        
        print(f"\nIn first 100 items:")
        print(f"  Recent dates (within 60 days): {len(recent_dates)}")
        print(f"  Old dates (older than 60 days): {len(old_dates)}")
        
        if old_dates:
            print(f"\nSample of old dates found:")
            for i, old_date in enumerate(old_dates[:5]):
                days_old = (datetime.now() - datetime.strptime(old_date, "%Y-%m-%d %H:%M:%S")).days
                print(f"  {i+1}. {old_date} ({days_old} days old)")
        
        # Filter and transform like the real script does
        filtered_count = 0
        total_count = 0
        
        for item in api_data:
            if item.get("Order") != "TEST":  # Exclude TEST orders
                total_count += 1
                timestamp = item.get("TimeStamp", "N/A")
                if is_within_60_days(timestamp):
                    filtered_count += 1
        
        print(f"\nAfter processing full dataset:")
        print(f"  Total non-TEST items: {total_count}")
        print(f"  Items within 60 days: {filtered_count}")
        print(f"  Items filtered out: {total_count - filtered_count}")
        print(f"  Percentage kept: {filtered_count/total_count*100:.1f}%" if total_count > 0 else "  No data")
        
    except Exception as e:
        print(f"Error fetching from API: {e}")
    
    print("=" * 60)

if __name__ == "__main__":
    test_second_api()
