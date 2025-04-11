# app/progress/routes.py
from flask import Blueprint, jsonify, request
from ..models import User, LeaderboardProgress
from .. import db

progress_bp = Blueprint('progress', __name__)

@progress_bp.route('/levels', methods=['GET'])
def get_progress_levels():
    print("[+] get_progress_levels!!")
    user_token = request.headers.get('Authorization', '').split(' ')[-1]
    if user_token == 'guest' or user_token == '':
        return jsonify([{
            "level": 1,
            "completed": 0,
            "total": 10,
            "guesses": 0,
            "unlocked": True
        }])
    
    user = User.query.get(user_token)
    if not user:
        return jsonify({
            "error": True,
            "message": "User not found",
            "code": 404
        }), 404

    return jsonify(user.progress_levels)

@progress_bp.route('/complete', methods=['POST'])
def complete_level():
    if request.headers.get('Authorization', '').split(' ')[-1] == 'guest':
        return jsonify({
            "error": True,
            "message": "Guest users cannot update progress",
            "code": 403
        }), 403

    data = request.get_json()
    level = data.get('level')
    guesses = data.get('guesses')
    
    user = User.query.get(request.headers.get('Authorization').split(' ')[-1])
    level_info = next((lvl for lvl in user.progress_levels if lvl['level'] == level), None)
    level_info['guesses'] = guesses
    level_info['completed'] = level_info['total']
    
    new_level = level + 1
    if not any(l['level'] == new_level for l in user.progress_levels):
        user.progress_levels.append({
            "level": new_level,
            "completed": 0,
            "total": 10,
            "guesses": 0,
            "unlocked": True
        })
    
    total_guesses = sum(l['guesses'] for l in user.progress_levels if l['completed'])
    avg_guesses = total_guesses / len(user.progress_levels) if user.progress_levels else 0
    progress_lb = LeaderboardProgress.query.get(user.token)
    progress_lb.avg_guesses = avg_guesses
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "nextLevel": new_level,
        "unlocked": True
    })