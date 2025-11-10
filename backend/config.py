import os
from datetime import timedelta

class Config:
    """Base configuration"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'zeitec-verifier-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://zeitec_user:zeitec_password@localhost:5432/zeitec_verifier'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'zeitec-jwt-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # File uploads
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', './uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    ALLOWED_EXTENSIONS = {'csv', 'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # Countries
    ALLOWED_COUNTRIES = ['Nigeria', 'Benin', 'Ghana', 'Kenya', 'South Africa']
    
    # Device capacity limit (kW)
    MAX_DEVICE_CAPACITY_KW = 250
    
    # CSV validation
    MAX_CSV_ROWS = 10000
    REQUIRED_DEVICE_REGISTRY_COLUMNS = [
        'deviceId', 'facilityId', 'serialNumber', 'manufacturer', 
        'model', 'capacityKW', 'technology', 'country', 
        'gridConnectionPoint', 'commissioningDate'
    ]
    REQUIRED_ISSUANCE_PERIOD_COLUMNS = [
        'deviceId', 'timestamp', 'kWh', 'auditTrailId'
    ]


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # In production, these MUST be set via environment variables
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://zeitec_user:zeitec_password@localhost:5432/zeitec_verifier_test'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
