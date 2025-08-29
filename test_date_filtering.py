#!/usr/bin/env python3
"""
Test script to verify the 60-day filtering logic is working correctly.
"""

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

def test_date_filtering():
    """Test the date filtering with sample data"""
    print("Testing 60-day date filtering logic...")
    
    current_date = datetime.now()
    sixty_days_ago = current_date - timedelta(days=60)
    
    print(f"Current date: {current_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"60 days ago: {sixty_days_ago.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test dates
    test_dates = [
        "2025-08-29 10:00:00",    # Should be kept (today)
        "2025-07-01 10:00:00",    # Should be kept (within 60 days)
        "2025-06-30 10:00:00",    # Should be kept (exactly 60 days ago)
        "2025-06-29 10:00:00",    # Should be removed (older than 60 days)
        "2024-07-10 13:33:40",    # Should be removed (way too old)
        "2025-02-26T00:00:00",    # Should be removed (older than 60 days)
        "2025-07-14T00:00:00",    # Should be kept (within 60 days)
        "invalid-date",           # Should be removed (invalid)
        "N/A",                    # Should be removed (N/A)
    ]
    
    for test_date in test_dates:
        result = is_within_60_days(test_date)
        status = "✅ KEEP" if result else "❌ REMOVE"
        print(f"{status}: {test_date}")
    
    print()
    
    # Check actual file samples
    files_to_check = ["test.json", "second.json"]
    
    for filename in files_to_check:
        try:
            print(f"Checking sample dates from {filename}:")
            with open(filename, "r") as f:
                data = json.load(f)
            
            sample_count = min(5, len(data.get("value", [])))
            for i in range(sample_count):
                item = data["value"][i]
                date_str = item.get("MtlQueue_NeedByDate", "N/A")
                result = is_within_60_days(date_str)
                status = "✅ VALID" if result else "❌ INVALID"
                print(f"  {status}: {date_str}")
            
            print()
            
        except Exception as e:
            print(f"Error checking {filename}: {e}")
            print()

if __name__ == "__main__":
    test_date_filtering()
