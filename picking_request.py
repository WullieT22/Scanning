import requests
from requests.auth import HTTPBasicAuth
import json
import logging
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
import urllib3
from datetime import datetime, timedelta
import os
from functools import lru_cache
import time
import sys

# Disable SSL warnings (since the API uses self-signed certificate)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Authentication
auth_wests = HTTPBasicAuth("WESTS", "Westfield")

def is_within_75_days(date_string):
    """Check if a date is within the last 75 days from today"""
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
        
        # Calculate the date 75 days ago
        seventy_five_days_ago = datetime.now() - timedelta(days=75)
        
        # Return True if the date is within the last 75 days
        return parsed_date >= seventy_five_days_ago
        
    except Exception as e:
        logging.error(f"Error parsing date {date_string}: {str(e)}")
        return False

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

def setup_logging():
    """Configure logging for the application"""
    if not os.path.exists("logs"):
        os.makedirs("logs")

    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(f'logs/api_fetch_{datetime.now().strftime("%Y%m%d")}.log'),
            logging.StreamHandler()
        ]
    )

def create_session():
    """Create a session with retry logic"""
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries, pool_connections=100, pool_maxsize=100)
    session.mount("https://", adapter)
    session.verify = False
    return session

def make_api_request(url, username, password):
    """Make a direct API request without caching"""
    auth = HTTPBasicAuth(username, password)
    session = create_session()
    return session.get(url, auth=auth, timeout=30)  # Add 30-second timeout

def fetch_additional_data():
    """Fetch data from EOL Picking List endpoint"""
    url = "https://199.5.83.159/EpicorERP/api/v1/BaqSvc/EOL_Picking_List/"
    username = "WESTS"
    password = "Westfield"

    try:
        response = make_api_request(url, username, password)
        response.raise_for_status()
        new_data = response.json()

        # Filter data to only include records within 60 days
        filtered_value = []
        original_count = len(new_data.get("value", []))
        
        for item in new_data.get("value", []):
            need_by_date = item.get("MtlQueue_NeedByDate")
            if is_within_60_days(need_by_date):
                filtered_value.append(item)
        
        logging.info(f"Filtered {original_count} records down to {len(filtered_value)} records within 60 days")
        
        # Update the data structure with filtered items
        new_data["value"] = filtered_value

        # Handle test.json with duplicate checking
        try:
            # Try to read existing data
            with open("test.json", "r") as infile:
                existing_data = json.load(infile)
                # Count unique Calculated_Test values
                unique_existing = len({item.get('Calculated_Test') for item in existing_data.get('value', []) if item.get('Calculated_Test')})
                logging.info(f"Current unique orders in file: {unique_existing}")
        except (FileNotFoundError, json.JSONDecodeError):
            # If file doesn't exist or is invalid, start with empty structure
            existing_data = {"value": [], "odata.metadata": new_data.get("odata.metadata", "")}
            unique_existing = 0
            logging.info("No existing file found, starting fresh")

        # Get existing Calculated_Test values
        existing_test_values = {item.get("Calculated_Test") for item in existing_data.get("value", [])}

        # Filter out new items that have duplicate Calculated_Test values
        new_items = [item for item in new_data.get("value", []) 
                    if item.get("Calculated_Test") not in existing_test_values]

        # Count unique new Calculated_Test values
        unique_new = len({item.get('Calculated_Test') for item in new_items if item.get('Calculated_Test')})

        # Append new items to existing data
        if new_items:
            # Add timestamp to each new item
            current_time = datetime.now().isoformat()
            for item in new_items:
                item["Added_Timestamp"] = current_time
            
            existing_data["value"].extend(new_items)
            with open("test.json", "w") as outfile:
                json.dump(existing_data, outfile, indent=4, sort_keys=True)
            
            # Display new items in command prompt
            logging.info(f"\nFound {unique_new} new unique orders:")
            for item in new_items:
                logging.info("-" * 50)
                logging.info(f"Order Number: {item.get('Calculated_Test', 'N/A')}")
                logging.info(f"Warehouse: {item.get('Calculated_Warehouse', 'N/A')}")
                logging.info(f"Part Number: {item.get('MtlQueue_PartNum', 'N/A')}")
                logging.info(f"Quantity: {item.get('Calculated_Quantity', 'N/A')}")
                logging.info(f"Ship To: {item.get('ShipTo_Name', 'N/A')}")
                logging.info(f"Need By Date: {item.get('MtlQueue_NeedByDate', 'N/A')}")
            logging.info("-" * 50)
            # Count total unique orders after append
            total_unique = len({item.get('Calculated_Test') for item in existing_data.get('value', []) if item.get('Calculated_Test')})
            logging.info(f"Total unique orders after append: {total_unique}")
        else:
            logging.info("No new unique orders to append")
            logging.info(f"Total unique orders remains: {unique_existing}")

    except Exception as e:
        logging.error(f"Error fetching data from {url}: {str(e)}")

def fetch_second_api():
    """Fetch data from second API endpoint - get ALL records"""
    url = "http://199.5.83.167:8000/picked"
    
    try:
        logging.info(f"Requesting ALL data from {url}")
        response = requests.get(url, timeout=120)  # Increase timeout for large response
        response.raise_for_status()
        new_data_list = response.json()
        logging.info(f"Received {len(new_data_list)} items from API")

        # Filter out any records with Order = "TEST"
        filtered_new_data = [item for item in new_data_list if item.get("Order") != "TEST"]
        if len(filtered_new_data) < len(new_data_list):
            logging.info(f"Filtered out {len(new_data_list) - len(filtered_new_data)} TEST records")
        
        # Transform data to match existing structure WITH new LotNum field
        transformed_data = []
        for item in filtered_new_data:
            transformed_item = {
                "Calculated_Test": item.get("Order", "N/A"),
                "Calculated_Warehouse": item.get("Location", "N/A"),
                # Keep the original product value in MtlQueue_PartNum
                "MtlQueue_PartNum": item.get("Product", "N/A"),
                # Add a new field for the extracted 8 digits
                "LotNum": extract_first_eight_from_last_sixteen(item.get("Product", "N/A")),
                "Calculated_Quantity": item.get("ExpectedQuantity", "N/A"),
                "ShipTo_Name": item.get("ShipAddress", "N/A"),
                "MtlQueue_NeedByDate": item.get("TimeStamp", "N/A")
            }
            
            # Filter based on 60-day rule
            need_by_date = transformed_item.get("MtlQueue_NeedByDate")
            if is_within_60_days(need_by_date):
                transformed_data.append(transformed_item)
        
        logging.info(f"After 60-day filtering: {len(transformed_data)} items remain from {len(filtered_new_data)} total items")
        
        filtered_data = {
            "value": transformed_data,
            "odata.metadata": ""
        }

        # When starting fresh, don't try to merge with existing file
        with open("second.json", "w") as outfile:
            json.dump(filtered_data, outfile, indent=4, sort_keys=True)
        
        logging.info(f"Written {len(filtered_data['value'])} items to second.json")
        return True

    except Exception as e:
        logging.error(f"Error fetching data from second API {url}: {str(e)}")
        return False

def extract_first_eight_from_last_sixteen(part_num):
    """Extract the first 8 digits from the last 16 digits of a part number"""
    try:
        # Make sure it's a string
        part_num = str(part_num)
        
        # Skip specific values that are known to cause issues
        if part_num == "TEST" or len(part_num) < 8:
            return ""  # Return empty string instead of the original value
        
        # If the part number is less than 16 characters but at least 8
        if len(part_num) < 16:
            # Just return the last 8 characters
            return part_num[-8:]
        
        # Extract the last 16 digits
        last_sixteen = part_num[-16:]
        
        # Take the first 8 of those digits
        first_eight = last_sixteen[:8]
        
        return first_eight
    except Exception as e:
        logging.error(f"Error extracting digits from part number: {str(e)}")
        return ""  # Return empty string on any error

def fetch_shipped_orders():
    """Fetch data from EOL Shipped Orders endpoint"""
    url = "https://199.5.83.159/EpicorERP/api/v1/BaqSvc/EOL_Shipped_Orders/"
    username = "WESTS"
    password = "Westfield"

    try:
        response = make_api_request(url, username, password)
        response.raise_for_status()
        new_data = response.json()

        # Filter data to only include records within 75 days
        filtered_value = []
        original_count = len(new_data.get("value", []))
        
        for item in new_data.get("value", []):
            # Check multiple date fields for 75-day filter
            ship_date = item.get("ShipHead_ShipDate")
            request_date = item.get("OrderDtl_RequestDate")
            actual_ship_date = item.get("Calculated_ActualShipDate")
            
            # Use ship date first, then request date, then actual ship date
            date_to_check = ship_date or request_date or actual_ship_date
            
            if is_within_75_days(date_to_check):
                filtered_value.append(item)
        
        logging.info(f"Filtered {original_count} shipped records down to {len(filtered_value)} records within 75 days")
        
        # Update the data structure with filtered items
        new_data["value"] = filtered_value

        # Handle shipped.json with duplicate checking
        try:
            # Try to read existing data
            with open("shipped.json", "r") as infile:
                existing_data = json.load(infile)
                # Count unique ShipDtl_OrderNum values
                unique_existing = len({item.get('ShipDtl_OrderNum') for item in existing_data.get('value', []) if item.get('ShipDtl_OrderNum')})
                logging.info(f"Current unique shipped orders in file: {unique_existing}")
        except (FileNotFoundError, json.JSONDecodeError):
            # If file doesn't exist or is invalid, start with empty structure
            existing_data = {"value": [], "odata.metadata": new_data.get("odata.metadata", "")}
            unique_existing = 0
            logging.info("No existing shipped.json file found, starting fresh")

        # Get existing ShipDtl_OrderNum values
        existing_order_numbers = {item.get("ShipDtl_OrderNum") for item in existing_data.get("value", [])}

        # Filter out new items that have duplicate ShipDtl_OrderNum values
        new_items = [item for item in new_data.get("value", []) 
                    if item.get("ShipDtl_OrderNum") not in existing_order_numbers]

        # Count unique new ShipDtl_OrderNum values
        unique_new = len({item.get('ShipDtl_OrderNum') for item in new_items if item.get('ShipDtl_OrderNum')})

        # Append new items to existing data
        if new_items:
            # Add timestamp to each new item
            current_time = datetime.now().isoformat()
            for item in new_items:
                item["Added_Timestamp"] = current_time
            
            existing_data["value"].extend(new_items)
            with open("shipped.json", "w") as outfile:
                json.dump(existing_data, outfile, indent=4, sort_keys=True)
            
            # Display new items in command prompt
            logging.info(f"\nFound {unique_new} new unique shipped orders:")
            for item in new_items:
                logging.info("-" * 50)
                logging.info(f"Order Number: {item.get('ShipDtl_OrderNum', 'N/A')}")
                logging.info(f"Part Number: {item.get('ShipDtl_PartNum', 'N/A')}")
                logging.info(f"Quantity: {item.get('ShipDtl_OurinventoryShipQty', 'N/A')}")
                logging.info(f"Need By Date: {item.get('OrderDtl_RequestDate', 'N/A')}")
                logging.info(f"Shipped On Date: {item.get('ShipHead_ShipDate', 'N/A')}")
                logging.info(f"Shipped By: {item.get('ShipHead_ShipPerson', 'N/A')}")
            logging.info("-" * 50)
            # Count total unique orders after append
            total_unique = len({item.get('ShipDtl_OrderNum') for item in existing_data.get('value', []) if item.get('ShipDtl_OrderNum')})
            logging.info(f"Total unique shipped orders after append: {total_unique}")
        else:
            logging.info("No new unique shipped orders to append")
            logging.info(f"Total unique shipped orders remains: {unique_existing}")

    except Exception as e:
        logging.error(f"Error fetching data from shipped orders API {url}: {str(e)}")

def is_business_hours():
    """Check if current time is between 6 AM and 8 PM"""
    # FOR TESTING: Always return True to ensure polling works
    return True
    
    # Original code
    # current_hour = datetime.now().hour
    # return 6 <= current_hour < 20

def clean_old_data_from_json_files():
    """Remove data older than 60/75 days from existing JSON files"""
    files_to_clean = [
        {"filename": "test.json", "days": 60, "date_field": "MtlQueue_NeedByDate"},
        {"filename": "second.json", "days": 60, "date_field": "MtlQueue_NeedByDate"},
        {"filename": "shipped.json", "days": 75, "date_field": "ShipHead_ShipDate"}
    ]
    
    for file_config in files_to_clean:
        filename = file_config["filename"]
        days = file_config["days"]
        date_field = file_config["date_field"]
        
        try:
            if not os.path.exists(filename):
                logging.info(f"{filename} does not exist, skipping cleanup")
                continue
                
            with open(filename, "r") as infile:
                data = json.load(infile)
            
            original_count = len(data.get("value", []))
            
            # Filter to keep only data within the specified days
            filtered_value = []
            for item in data.get("value", []):
                date_to_check = item.get(date_field)
                
                # For shipped.json, also check alternative date fields
                if filename == "shipped.json" and not date_to_check:
                    date_to_check = item.get("OrderDtl_RequestDate") or item.get("Calculated_ActualShipDate")
                
                # Use appropriate date checking function
                if days == 75:
                    keep_item = is_within_75_days(date_to_check)
                else:
                    keep_item = is_within_60_days(date_to_check)
                
                if keep_item:
                    filtered_value.append(item)
            
            data["value"] = filtered_value
            new_count = len(filtered_value)
            
            if original_count != new_count:
                with open(filename, "w") as outfile:
                    json.dump(data, outfile, indent=4, sort_keys=True)
                logging.info(f"Cleaned {filename}: removed {original_count - new_count} old records, {new_count} records remain")
            else:
                logging.info(f"{filename}: no old records to remove, {new_count} records remain")
                
        except Exception as e:
            logging.error(f"Error cleaning {filename}: {str(e)}")

def ensure_json_file_exists(filename):
    """Ensure a JSON file exists with at least an empty structure"""
    try:
        with open(filename, "r") as test_file:
            # File exists, no need to do anything
            pass
    except (FileNotFoundError, json.JSONDecodeError):
        # Create an empty JSON structure
        empty_data = {"value": [], "odata.metadata": ""}
        with open(filename, "w") as outfile:
            json.dump(empty_data, outfile)
        logging.info(f"Created empty {filename} file")

def main():
    setup_logging()
    polling_interval = 120  # 2 minutes in seconds
    logging.info("==== SCRIPT STARTED ====")  # Clear indicator
    logging.info(f"Starting API fetch script - polling every {polling_interval} seconds continuously")
    
    try:
        while True:
            # Track which APIs succeeded
            apis_succeeded = 0
            apis_attempted = 0
            
            current_time = datetime.now()
            logging.info(f"==== POLLING CYCLE STARTED: {current_time.strftime('%H:%M:%S')} ====")
            
            try:
                start_time = datetime.now()
                
                # Clean old data from JSON files at the start of each cycle
                try:
                    logging.info("Cleaning old data from JSON files...")
                    clean_old_data_from_json_files()
                    logging.info("Cleanup completed")
                except Exception as e:
                    logging.error(f"Error during cleanup: {str(e)}")
                
                # Try each API separately so one failure doesn't stop others
                try:
                    apis_attempted += 1
                    logging.info("Starting fetch_additional_data()...")
                    fetch_additional_data()
                    logging.info("fetch_additional_data() completed successfully")
                    apis_succeeded += 1
                except Exception as e:
                    logging.error(f"Error in fetch_additional_data(): {str(e)}")
                
                try:
                    apis_attempted += 1
                    logging.info("Starting fetch_second_api()...")
                    fetch_second_api()
                    logging.info("fetch_second_api() completed successfully")
                    apis_succeeded += 1
                except Exception as e:
                    logging.error(f"Error in fetch_second_api(): {str(e)}")
                
                try:
                    apis_attempted += 1
                    logging.info("Starting fetch_shipped_orders()...")
                    fetch_shipped_orders()  
                    logging.info("fetch_shipped_orders() completed successfully")
                    apis_succeeded += 1
                except Exception as e:
                    logging.error(f"Error in fetch_shipped_orders(): {str(e)}")
                
                # Log overall success/failure
                if apis_succeeded == apis_attempted:
                    logging.info("All API calls completed successfully")
                else:
                    logging.warning(f"{apis_succeeded}/{apis_attempted} API calls succeeded")
                
                # Calculate how long the processing took
                processing_time = (datetime.now() - start_time).total_seconds()
                logging.info(f"Processing took {processing_time:.2f} seconds")
                
                # Adjust sleep time to maintain 2-minute intervals
                sleep_time = max(1, polling_interval - processing_time)  # Ensure at least 1 second
                logging.info(f"Waiting {sleep_time:.2f} seconds until next poll...")
                time.sleep(sleep_time)
                
            except requests.exceptions.RequestException as e:
                logging.error(f"Network error occurred: {str(e)}")
                logging.info(f"Will retry in {polling_interval} seconds...")
                time.sleep(polling_interval)
            except Exception as e:
                logging.error(f"Unexpected error occurred: {str(e)}", exc_info=True)
                logging.info(f"Will retry in {polling_interval} seconds...")
                time.sleep(polling_interval)
                
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt, shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()