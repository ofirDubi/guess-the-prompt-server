# app/auth/routes.py
from flask import Blueprint, jsonify, request
from .. import db
from ..models import User
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password_hash = data.get('password')

    if username == 'guest':
        return jsonify({
            "error": True,
            "message": "Username 'guest' is reserved",
            "code": 400
        }), 400

    if User.query.filter_by(username=username).first():
        return jsonify({
            "error": True,
            "message": "Username already exists",
            "code": 400
        }), 400

    token = str(uuid.uuid4())
    new_user = User(
        token=token,
        username=username,
        password_hash=password_hash,
        progress_levels=[{
            "level": 1,
            "completed": 0,
            "total": 10,
            "guesses": 0,
            "unlocked": True
        }]
    )
    
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "id": token,
        "username": username,
        "casualScore": 0,
        "dailyScore": 0,
        "token": token,
        "progressLevels": new_user.progress_levels
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password_hash = data.get('password')

    user = User.query.filter_by(username=username).first()
    if not user or user.password_hash != password_hash:
        return jsonify({
            "error": True,
            "message": "Invalid credentials",
            "code": 401
        }), 401

    return jsonify({
        "id": user.token,
        "username": user.username,
        "casualScore": user.casual_score,
        "dailyScore": user.daily_score,
        "token": user.token,
        "progressLevels": user.progress_levels
    }), 200