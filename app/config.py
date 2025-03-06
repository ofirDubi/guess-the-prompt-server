# app/config.py
import os

class Config:
    # DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///guess_the_prompt.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')