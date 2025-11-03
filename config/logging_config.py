"""Logging configuration for the AQI Prediction System"""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Log file paths
COLLECTION_LOG = os.path.join(LOGS_DIR, 'data_collection.log')
API_LOG = os.path.join(LOGS_DIR, 'api_requests.log')
DB_LOG = os.path.join(LOGS_DIR, 'database.log')
ERROR_LOG = os.path.join(LOGS_DIR, 'errors.log')

def setup_logger(name, log_file, level=logging.INFO, max_size=5*1024*1024, backup_count=5):
    """
    Set up a logger with both file and console handlers
    
    Args:
        name (str): Logger name
        log_file (str): Path to log file
        level (int): Logging level
        max_size (int): Maximum size of log file before rotation (default: 5MB)
        backup_count (int): Number of backup files to keep
    
    Returns:
        logging.Logger: Configured logger instance
    """
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear any existing handlers
    logger.handlers = []
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Create loggers
collection_logger = setup_logger('data_collection', COLLECTION_LOG)
api_logger = setup_logger('api_requests', API_LOG)
db_logger = setup_logger('database', DB_LOG)
error_logger = setup_logger('errors', ERROR_LOG, level=logging.ERROR)

def log_error(logger_name, error_message, exc_info=None):
    """
    Log error to both specific logger and error log
    
    Args:
        logger_name (str): Name of the specific logger
        error_message (str): Error message to log
        exc_info (Exception, optional): Exception info to include
    """
    # Log to specific logger
    logger = logging.getLogger(logger_name)
    logger.error(error_message, exc_info=exc_info)
    
    # Also log to error logger
    error_logger.error(
        f"[{logger_name}] {error_message}",
        exc_info=exc_info
    )

def get_logger(name):
    """
    Get an existing logger by name
    
    Args:
        name (str): Logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)

class LoggerAdapter(logging.LoggerAdapter):
    """Custom adapter to add context to log messages"""
    
    def process(self, msg, kwargs):
        """Add timestamp and optional context to message"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if 'city' in self.extra:
            msg = f"[{timestamp}] [{self.extra['city']}] {msg}"
        else:
            msg = f"[{timestamp}] {msg}"
            
        return msg, kwargs

def get_city_logger(logger_name, city):
    """
    Get a logger with city context
    
    Args:
        logger_name (str): Base logger name
        city (str): City name for context
        
    Returns:
        LoggerAdapter: Logger with city context
    """
    logger = get_logger(logger_name)
    return LoggerAdapter(logger, {'city': city})