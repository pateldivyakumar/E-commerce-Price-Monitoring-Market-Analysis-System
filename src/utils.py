import os
import psycopg2
from dotenv import load_dotenv
import logging

def setup_logging(log_file="logs/pipeline.log"):
    """Sets up structured logging to both file and console."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logger = logging.getLogger("price_monitor")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console Handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File Handler
        try:
            fh = logging.FileHandler(log_file, encoding='utf-8')
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception as e:
            print(f"Warning: Could not set up file logging: {e}")

    return logger

def get_db_connection(database=None):
    """
    Returns a connection to the PostgreSQL database.
    If database=None, connects to the specific database in .env.
    Otherwise, connects to the specified database (e.g. 'postgres' for DDL).
    """
    load_dotenv()
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")
    
    db_name = database if database else os.getenv("DB_NAME", "price_monitor")
    
    return psycopg2.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name
    )

def get_db_config():
    """Returns the expected database name."""
    load_dotenv()
    return os.getenv("DB_NAME", "price_monitor")
