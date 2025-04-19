import os

class Config:
    """Base configuration class."""
    # Flask settings
    SECRET_KEY = os.environ.get("SESSION_SECRET", "dev-key-for-jockey-wms")
    
    # Database settings
    DATABASE_TYPE = os.environ.get("DATABASE_TYPE", "sqlite")
    
    if DATABASE_TYPE == "mysql":
        # MySQL database configuration
        SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    else:
        # SQLite database configuration (default)
        SQLALCHEMY_DATABASE_URI = 'sqlite:///jockey_wms.sqlite'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join('static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max upload size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Pagination
    PER_PAGE = 10

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

# Use Development config by default
Config = DevelopmentConfig
