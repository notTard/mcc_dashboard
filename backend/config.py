import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # PostgreSQL конфигурация
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'gvc_dashboard')
    DB_USER = os.getenv('DB_USER', 'gvc_user')
    DB_PASS = os.getenv('DB_PASS', 'gvc_password123')
    
    # Строка подключения
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')