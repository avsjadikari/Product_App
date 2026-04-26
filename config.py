"""
Configuration management for the POS application.
Supports .env files with validation and sensible defaults.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

CONFIG_FILE = Path(__file__).parent / "config.json"


class Config:
    """Application configuration with environment variable support."""

    SECRET_KEY: str = os.environ.get(
        "SECRET_KEY", "dev-secret-key-change-in-production"
    )
    DEBUG: bool = (
        os.environ.get("FLASK_DEBUG", os.environ.get("DEBUG", "False")).lower()
        == "true"
    )
    FLASK_ENV: str = os.environ.get("FLASK_ENV", "development")
    TESTING: bool = False

    DB_USER: str = os.environ.get("DB_USER", "postgres")
    DB_PASSWORD: str = os.environ.get("DB_PASSWORD", "")
    DB_HOST: str = os.environ.get("DB_HOST", "localhost")
    DB_PORT: str = os.environ.get("DB_PORT", "5432")
    DB_NAME: str = os.environ.get("DB_NAME", "product")

    _db_config: Dict[str, str] = {}

    @classmethod
    def load_config(cls) -> Dict[str, str]:
        """Load configuration from config file if exists."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    cls._db_config = json.load(f)
                    return cls._db_config
            except Exception:
                pass
        return {}

    @classmethod
    def save_config(cls, config: Dict[str, str]) -> bool:
        """Save configuration to config file."""
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)
            cls._db_config = config
            # Force reload from file to ensure consistency
            with open(CONFIG_FILE, "r") as f:
                cls._db_config = json.load(f)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    @classmethod
    def is_configured(cls) -> bool:
        """Check if database is configured."""
        config = cls.load_config()
        return bool(config.get("DB_HOST") and config.get("DB_NAME"))

    @classmethod
    def get_database_uri(cls, override_config: Optional[Dict[str, str]] = None) -> str:
        """Get database URI, optionally with override config."""
        if override_config:
            # Handle both lowercase and uppercase keys
            user = override_config.get("db_user") or override_config.get(
                "DB_USER", "postgres"
            )
            password = override_config.get("db_password") or override_config.get(
                "DB_PASSWORD", ""
            )
            host = override_config.get("db_host") or override_config.get(
                "DB_HOST", "localhost"
            )
            port = override_config.get("db_port") or override_config.get(
                "DB_PORT", "5432"
            )
            name = override_config.get("db_name") or override_config.get(
                "DB_NAME", "product"
            )
            return f"postgresql://{user}:{password}@{host}:{port}/{name}"

        if cls._db_config:
            user = cls._db_config.get("DB_USER", "postgres")
            password = cls._db_config.get("DB_PASSWORD", "")
            host = cls._db_config.get("DB_HOST", "localhost")
            port = cls._db_config.get("DB_PORT", "5432")
            name = cls._db_config.get("DB_NAME", "product")
            return f"postgresql://{user}:{password}@{host}:{port}/{name}"

        user = os.environ.get("DB_USER", "postgres")
        password = os.environ.get("DB_PASSWORD", "")
        host = os.environ.get("DB_HOST", "localhost")
        port = os.environ.get("DB_PORT", "5432")
        name = os.environ.get("DB_NAME", "product")
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"

    @classmethod
    def get_current_config(cls) -> Dict[str, str]:
        """Get current configuration for display."""
        if cls._db_config:
            return {
                "DB_HOST": cls._db_config.get("DB_HOST", "localhost"),
                "DB_PORT": cls._db_config.get("DB_PORT", "5432"),
                "DB_NAME": cls._db_config.get("DB_NAME", "product"),
                "DB_USER": cls._db_config.get("DB_USER", "postgres"),
                "SECRET_KEY": cls._db_config.get("SECRET_KEY", ""),
            }
        return {
            "DB_HOST": os.environ.get("DB_HOST", "localhost"),
            "DB_PORT": os.environ.get("DB_PORT", "5432"),
            "DB_NAME": os.environ.get("DB_NAME", "product"),
            "DB_USER": os.environ.get("DB_USER", "postgres"),
            "SECRET_KEY": os.environ.get("SECRET_KEY", ""),
        }

    DEFAULT_TAX_RATE: float = float(os.environ.get("DEFAULT_TAX_RATE", "0"))
    ITEMS_PER_PAGE: int = int(os.environ.get("ITEMS_PER_PAGE", "20"))
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.environ.get("LOG_FILE", "app.log")
    PERMANENT_SESSION_LIFETIME: int = int(
        os.environ.get("PERMANENT_SESSION_LIFETIME", "3600")
    )

    DEFAULT_ADMIN_USER: str = os.environ.get("DEFAULT_ADMIN_USER", "admin")
    DEFAULT_ADMIN_PASSWORD: str = os.environ.get("DEFAULT_ADMIN_PASSWORD", "admin123")
    DEFAULT_USER_USER: str = os.environ.get("DEFAULT_USER_USER", "user")
    DEFAULT_USER_PASSWORD: str = os.environ.get("DEFAULT_USER_PASSWORD", "user123")

    LOGIN_RATE_LIMIT: int = int(os.environ.get("LOGIN_RATE_LIMIT", "5"))
    LOGIN_RATE_WINDOW: int = int(os.environ.get("LOGIN_RATE_WINDOW", "300"))

    MAX_SEARCH_LENGTH: int = int(os.environ.get("MAX_SEARCH_LENGTH", "100"))

    JWT_SECRET_KEY: str = os.environ.get(
        "JWT_SECRET_KEY",
        os.environ.get("SECRET_KEY", "jwt-secret-change-in-production"),
    )
    JWT_ACCESS_TOKEN_EXPIRES: int = int(
        os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", "3600")
    )

    PASSWORD_MIN_LENGTH: int = int(os.environ.get("PASSWORD_MIN_LENGTH", "8"))
    PASSWORD_REQUIRE_UPPERCASE: bool = (
        os.environ.get("PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true"
    )
    PASSWORD_REQUIRE_LOWERCASE: bool = (
        os.environ.get("PASSWORD_REQUIRE_LOWERCASE", "true").lower() == "true"
    )
    PASSWORD_REQUIRE_DIGIT: bool = (
        os.environ.get("PASSWORD_REQUIRE_DIGIT", "true").lower() == "true"
    )
    PASSWORD_REQUIRE_SPECIAL: bool = (
        os.environ.get("PASSWORD_REQUIRE_SPECIAL", "true").lower() == "true"
    )

    WTF_CSRF_ENABLED: bool = (
        os.environ.get("WTF_CSRF_ENABLED", "true").lower() == "true"
    )
    WTF_CSRF_TIME_LIMIT: int = int(os.environ.get("WTF_CSRF_TIME_LIMIT", "3600"))

    @classmethod
    def validate(cls) -> Dict[str, Any]:
        issues = []
        if not cls.is_configured() and not os.environ.get("DB_HOST"):
            return {"valid": True, "issues": []}

        if cls.SECRET_KEY == "dev-secret-key-change-in-production":
            if not cls.is_configured():
                issues.append("Database not configured - setup required")
        if cls.DEBUG and os.environ.get("FLASK_ENV") == "production":
            issues.append("DEBUG is True in production mode")
        if not cls.DB_PASSWORD and not cls._db_config:
            issues.append("DB_PASSWORD is not set")
        if not cls.DB_HOST and not cls._db_config:
            issues.append("DB_HOST is not configured")
        if not cls.DB_NAME and not cls._db_config:
            issues.append("DB_NAME is not configured")
        if cls._db_config and cls.JWT_SECRET_KEY == "jwt-secret-change-in-production":
            issues.append("JWT_SECRET_KEY is using default value")
        return {"valid": len(issues) == 0, "issues": issues}

    @classmethod
    def init_app(cls, app) -> None:
        config = cls.load_config()

        if config:
            app.config["SECRET_KEY"] = config.get("SECRET_KEY", cls.SECRET_KEY)
            app.config["SQLALCHEMY_DATABASE_URI"] = cls.get_database_uri()
        else:
            app.config["SECRET_KEY"] = cls.SECRET_KEY

        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        app.config["DEFAULT_TAX_RATE"] = cls.DEFAULT_TAX_RATE
        app.config["ITEMS_PER_PAGE"] = cls.ITEMS_PER_PAGE
        app.config["PERMANENT_SESSION_LIFETIME"] = cls.PERMANENT_SESSION_LIFETIME
        app.config["WTF_CSRF_ENABLED"] = cls.WTF_CSRF_ENABLED
        app.config["WTF_CSRF_TIME_LIMIT"] = cls.WTF_CSRF_TIME_LIMIT
        cls._configure_logging(app)

    @classmethod
    def _configure_logging(cls, app) -> None:
        import logging
        from logging.handlers import RotatingFileHandler

        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(exist_ok=True)
        log_path = log_dir / cls.LOG_FILE

        file_handler = RotatingFileHandler(
            log_path, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        file_handler.setLevel(getattr(logging, cls.LOG_LEVEL))
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)

        app.logger.addHandler(file_handler)
        app.logger.setLevel(getattr(logging, cls.LOG_LEVEL))

        app_logger = logging.getLogger("app")
        app_logger.addHandler(file_handler)
        app_logger.setLevel(getattr(logging, cls.LOG_LEVEL))

        app.logger.info("=" * 60)
        app.logger.info("Application starting up")
        app.logger.info(f"Debug mode: {cls.DEBUG}")

        config = cls.load_config()
        if config:
            app.logger.info(
                f"Database: {config.get('DB_HOST')}:{config.get('DB_PORT')}/{config.get('DB_NAME')}"
            )
        else:
            app.logger.info(f"Database: {cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}")
        app.logger.info("=" * 60)


config_validation = Config.validate()
if not config_validation["valid"]:
    print("Configuration Issues:")
    for issue in config_validation["issues"]:
        print(f"  - {issue}")
