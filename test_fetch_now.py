# test_fetch_now.py
import importlib.util
import sys
import os

# Load the module with a space in the filename
script_path = os.path.join(os.path.dirname(__file__), "import requests3.py")
module_name = "import_requests3"

spec = importlib.util.spec_from_file_location(module_name, script_path)
module = importlib.util.module_from_spec(spec)
sys.modules[module_name] = module
spec.loader.exec_module(module)

# Now access the functions
setup_logging = module.setup_logging
create_session = module.create_session
fetch_additional_data = module.fetch_additional_data
fetch_second_api = module.fetch_second_api

# Check if the function exists
if hasattr(module, 'fetch_shipped_orders'):
    fetch_shipped_orders = module.fetch_shipped_orders
else:
    print("WARNING: fetch_shipped_orders function not found in the module")
    fetch_shipped_orders = None

# Set up logging
setup_logging()

# Run all fetch functions once, ignoring time restrictions
print("Running one-time test fetch...")
session = create_session()
fetch_additional_data()
fetch_second_api()
if fetch_shipped_orders:
    fetch_shipped_orders()
print("Test fetch complete!")