import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
CPCB_API_KEY = os.getenv('CPCB_API_KEY')
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
IQAIR_API_KEY = os.getenv('IQAIR_API_KEY')

# API Base URLs
OPENWEATHER_BASE_URL = "http://api.openweathermap.org/data/2.5"
IQAIR_BASE_URL = "http://api.airvisual.com/v2"

# List of Indian cities to monitor
CITIES = [
    "Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", 
    "Hyderabad", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
    "Kanpur", "Nagpur", "Indore", "Thane", "Bhopal",
    "Visakhapatnam", "Pimpri-Chinchwad", "Patna", "Vadodara", "Ghaziabad",
    "Ludhiana", "Agra", "Nashik", "Faridabad", "Meerut",
    "Rajkot", "Varanasi", "Srinagar", "Aurangabad", "Dhanbad",
    "Amritsar", "Navi Mumbai", "Allahabad", "Ranchi", "Howrah",
    "Coimbatore", "Jabalpur", "Gwalior", "Vijayawada", "Jodhpur",
    "Madurai", "Raipur", "Kota", "Chandigarh", "Guwahati",
    "Solapur", "Hubli-Dharwad", "Bareilly", "Moradabad", "Mysore",
    "Gurgaon", "Aligarh", "Jalandhar", "Bhubaneswar", "Salem",
    "Warangal"
]

# Priority cities for more frequent monitoring
PRIORITY_CITIES = [
    "Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata",
    "Hyderabad", "Pune", "Ahmedabad"
]

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'aqi_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT', '5432')
}

# Data Collection Settings
COLLECTION_INTERVAL = 3600  # 1 hour in seconds
PRIORITY_COLLECTION_INTERVAL = 1800  # 30 minutes in seconds
PARALLEL_WORKERS = 4  # Number of parallel workers for data collection

# Extended cities list (including nearby cities and industrial areas)
EXTENDED_CITIES = CITIES + [
    "Noida", "Greater Noida", "Ghaziabad", "Faridabad", 
    "Bhiwadi", "Sonipat", "Panipat", "Alwar", "Bharatpur",
    "Mathura", "Meerut", "Rohtak", "Rewari", "Bhiwani"
]

# API Request Settings
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Logging Configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 5
