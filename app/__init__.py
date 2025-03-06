# app/__init__.py
from flask import Flask, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os
from flask_migrate import Migrate  # Import Flask-Migrate
import logging

db = SQLAlchemy()

# Global DataFrame for images
df_images = None


def create_app():
    # , static_folder=os.path.abspath('../data/selected_images')
    app = Flask(__name__)
    # print(os.path.abspath('../data/selected_images'))
    app.config.from_object('app.config.Config')

    API_KEY = "aaas9d98heljah2uiohad-jrggkisnm91"

    db.init_app(app)
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)

    # CORS(app, resources={r"/*": {"origins": ["http://localhost:5000", "http://guesstheprompt.site", "https://guesstheprompt.site"]}})
    CORS(app, resources={r"/*": {"origins": "http://localhost:8080"}})
    # limiter = Limiter(get_remote_address, app=app, default_limits=["100 per minute"])
    if app.config['DEBUG']:
        print("[+] Running Debug Mode!")    
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
            
        @app.before_request
        def log_request_data():
            # Log request details
            logger.debug(f"Request: {request.method} {request.path}")
            logger.debug(f"Headers: {dict(request.headers)}")
            if request.method in ['POST', 'PUT', 'PATCH']:
                logger.debug(f"Request Body: {request.get_json(silent=True)}")
        
        @app.after_request
        def log_response_data(response):
            # Log response details
            logger.debug(f"Response Status: {response.status_code}")
            try:
                # Attempt to log JSON response data
                response_data = response.get_json()
                logger.debug(f"Response Data: {response_data}")
            except Exception:
                # Log raw response data if not JSON
                logger.debug(f"Raw Response Data: {response.data}")
            return response


    # Load images CSV into a global DataFrame (only once)
    global df_images
    # print(os.getcwd())  
    if df_images is None:
        df_images = pd.read_csv('selected_images.csv')
    
    # Register blueprints
    from .auth.routes import auth_bp
    from .images.routes import images_bp
    from .progress.routes import progress_bp
    from .guesses.routes import guesses_bp
    from .leaderboard.routes import leaderboard_bp
    from .data.routes import data_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(images_bp, url_prefix='/api/images')
    app.register_blueprint(progress_bp, url_prefix='/api/progress')
    app.register_blueprint(guesses_bp, url_prefix='/api/guess')
    app.register_blueprint(leaderboard_bp, url_prefix='/api/leaderboard')
    app.register_blueprint(data_bp, url_prefix='/data/selected_images')

    return app