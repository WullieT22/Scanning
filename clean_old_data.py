#!/usr/bin/env python3
"""
Standalone script to clean old data (older than 60 days) from test.json and second.json files.
This script will filter the data based on MtlQueue_NeedByDate field.
"""

import json
import logging
from datetime import datetime, timedelta
import os

def setup_logging():
    """Configure logging for the application"""
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler()
        ]
    )

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
            logging.warning(f"Could not parse date: {date_string}")
            return False
        
        # Calculate the date 60 days ago
        sixty_days_ago = datetime.now() - timedelta(days=60)
        
        # Return True if the date is within the last 60 days
        return parsed_date >= sixty_days_ago
        
    except Exception as e:
        logging.error(f"Error parsing date {date_string}: {str(e)}")
        return False

def clean_json_file(filename):
    """Clean old data from a specific JSON file"""
    try:
        if not os.path.exists(filename):
            logging.info(f"{filename} does not exist, skipping")
            return
            
        logging.info(f"Processing {filename}...")
        
        with open(filename, "r") as infile:
            data = json.load(infile)
        
        original_count = len(data.get("value", []))
        
        # Filter to keep only data within 60 days
        filtered_value = []
        removed_dates = []
        
        for item in data.get("value", []):
            need_by_date = item.get("MtlQueue_NeedByDate")
            if is_within_60_days(need_by_date):
                filtered_value.append(item)
            else:
                removed_dates.append(need_by_date)
        
        data["value"] = filtered_value
        new_count = len(filtered_value)
        
        if original_count != new_count:
            # Create backup
            backup_filename = f"{filename}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with open(backup_filename, "w") as backup_file:
                with open(filename, "r") as original_file:
                    backup_file.write(original_file.read())
            
            # Write cleaned data
            with open(filename, "w") as outfile:
                json.dump(data, outfile, indent=4, sort_keys=True)
            
            logging.info(f"✅ {filename}: removed {original_count - new_count} old records, {new_count} records remain")
            logging.info(f"   Backup created: {backup_filename}")
            
            if removed_dates:
                logging.info(f"   Sample of removed dates: {removed_dates[:5]}")
        else:
            logging.info(f"✅ {filename}: no old records to remove, {new_count} records remain")
            
    except Exception as e:
        logging.error(f"❌ Error cleaning {filename}: {str(e)}")

def main():
    setup_logging()
    
    logging.info("=" * 60)
    logging.info("DATA CLEANUP SCRIPT - Removing records older than 60 days")
    logging.info("=" * 60)
    
    current_date = datetime.now()
    sixty_days_ago = current_date - timedelta(days=60)
    
    logging.info(f"Current date: {current_date.strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"Cutoff date (60 days ago): {sixty_days_ago.strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"Only keeping records with MtlQueue_NeedByDate >= {sixty_days_ago.strftime('%Y-%m-%d')}")
    logging.info("")
    
    # Clean both JSON files
    files_to_clean = ["test.json", "second.json"]
    
    for filename in files_to_clean:
        clean_json_file(filename)
        logging.info("")
    
    logging.info("=" * 60)
    logging.info("CLEANUP COMPLETED")
    logging.info("=" * 60)

if __name__ == "__main__":
    main()
