# app/images/routes.py
from flask import Blueprint, jsonify, request, url_for

from .. import df_images
from ..models import User
from datetime import datetime
import pandas as pd

images_bp = Blueprint('images', __name__)

@images_bp.route('/random', methods=['GET'])
def get_random_image():
    image = df_images.sample().iloc[0]
    
    return jsonify({
        "id": image['id'],
        "imageUrl": request.url_root  + image['image_url'],
        "promptLength": len(image['prompt'].split())
    })

@images_bp.route('/daily', methods=['GET'])
def get_daily_image():
    today = datetime.now().date()
    daily_images = df_images[df_images['type'] == 'daily']
    if daily_images.empty:
        return jsonify({
            "error": True,
            "message": "No daily images available",
            "code": 404
        }), 404

    daily_image = daily_images.sample(
        random_state=int(today.toordinal())
    ).iloc[0]
    
    user_token = request.headers.get('Authorization', '').split(' ')[-1]
    has_submitted = False
    if user_token and user_token != 'guest':
        user = User.query.get(user_token)
        if user:
            has_submitted = user.last_submission_date == today

    return jsonify({
        "id": daily_image['id'],
        "imageUrl": daily_image['image_url'],
        "promptLength": len(daily_image['prompt'].split()),
        "hasSubmittedToday": has_submitted
    })

@images_bp.route('/progress/<int:level>', methods=['GET'])
def get_progress_image(level):
    user_token = request.headers.get('Authorization', '').split(' ')[-1]
    user = User.query.get(user_token) if user_token != 'guest' else None

    if not user:
        return jsonify({
            "error": True,
            "message": "User not found",
            "code": 404
        }), 404

    level_info = next((lvl for lvl in user.progress_levels if lvl['level'] == level), None)
    if not level_info or not level_info['unlocked']:
        return jsonify({
            "error": True,
            "message": "Level not unlocked",
            "code": 403
        }), 403

    image_number = level_info['completed'] + 1
    image = df_images[
        (df_images['level'] == level) & 
        (df_images['image_number'] == image_number)
    ]

    if image.empty:
        return jsonify({
            "error": True,
            "message": "Image not found",
            "code": 404
        }), 404

    image = image.iloc[0]

    return jsonify({
        "id": image['id'],
        "imageUrl": image['image_url'],
        "promptLength": len(image['prompt'].split()),
        "level": level,
        "imageNumber": image_number,
        "totalImagesInLevel": level_info['total']
    })