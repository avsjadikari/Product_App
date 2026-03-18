"""
Configuration management for the POS application.
Supports .env files with validation and sensible defaults.
"""
import os
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)


class Config:
    """Application configuration with environment variable support."""
    
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG: bool = os.environ.get('DEBUG', 'True').lower() == 'true'
    TESTING: bool = False
    
    # Database settings
    DB_USER: str = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD: str = os.environ.get('DB_PASSWORD', '')
    DB_HOST: str = os.environ.get('DB_HOST', 'localhost')
    DB_PORT: str = os.environ.get('DB_PORT', '5432')
    DB_NAME: str = os.environ.get('DB_NAME', 'product')
    
    @staticmethod
    def get_database_uri() -> str:
        user = os.environ.get('DB_USER', 'postgres')
        password = os.environ.get('DB_PASSWORD', '')
        host = os.environ.get('DB_HOST', 'localhost')
        port = os.environ.get('DB_PORT', '5432')
        name = os.environ.get('DB_NAME', 'product')
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"
    
    # Application settings
    DEFAULT_TAX_RATE: float = float(os.environ.get('DEFAULT_TAX_RATE', '0'))
    ITEMS_PER_PAGE: int = int(os.environ.get('ITEMS_PER_PAGE', '20'))
    LOG_LEVEL: str = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.environ.get('LOG_FILE', 'app.log')
    PERMANENT_SESSION_LIFETIME: int = 3600
    
    @classmethod
    def validate(cls) -> Dict[str, Any]:
        issues = []
        if cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            issues.append("SECRET_KEY is using default value - change in production")
        if cls.DEBUG and os.environ.get('FLASK_ENV') == 'production':
            issues.append("DEBUG is True in production mode")
        if not cls.DB_PASSWORD:
            issues.append("DB_PASSWORD is not set")
        if not cls.DB_HOST:
            issues.append("DB_HOST is not configured")
        if not cls.DB_NAME:
            issues.append("DB_NAME is not configured")
        return {'valid': len(issues) == 0, 'issues': issues}
    
    @classmethod
    def init_app(cls, app) -> None:
        app.config['SECRET_KEY'] = cls.SECRET_KEY
        app.config['SQLALCHEMY_DATABASE_URI'] = cls.get_database_uri()
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['DEFAULT_TAX_RATE'] = cls.DEFAULT_TAX_RATE
        app.config['ITEMS_PER_PAGE'] = cls.ITEMS_PER_PAGE
        app.config['PERMANENT_SESSION_LIFETIME'] = cls.PERMANENT_SESSION_LIFETIME
        cls._configure_logging(app)
    
    @classmethod
    def _configure_logging(cls, app) -> None:
        import logging
        from logging.handlers import RotatingFileHandler
        
        log_dir = Path(__file__).parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        log_path = log_dir / cls.LOG_FILE
        
        file_handler = RotatingFileHandler(log_path, maxBytes=10*1024*1024, backupCount=5)
        file_handler.setLevel(getattr(logging, cls.LOG_LEVEL))
        formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(getattr(logging, cls.LOG_LEVEL))
        app.logger.info("=" * 60)
        app.logger.info("Application starting up")
        app.logger.info(f"Debug mode: {cls.DEBUG}")
        app.logger.info(f"Database: {cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}")
        app.logger.info("=" * 60)


config_validation = Config.validate()
if not config_validation['valid']:
    print("Configuration Issues:")
    for issue in config_validation['issues']:
        print(f"  - {issue}")