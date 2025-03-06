# app/leaderboard/routes.py
from flask import Blueprint, jsonify
from ..models import LeaderboardCasual, LeaderboardDaily, LeaderboardProgress, User

leaderboard_bp = Blueprint('leaderboard', __name__)

@leaderboard_bp.route('/<string:mode>', methods=['GET'])
def get_leaderboard(mode):
    if mode == 'casual':
        entries = LeaderboardCasual.query.order_by(LeaderboardCasual.score.desc()).all()
        results = [{
            "rank": i+1,
            "username": User.query.get(e.user_id).username,
            "score": e.score
        } for i, e in enumerate(entries)]
    elif mode == 'daily':
        entries = LeaderboardDaily.query.order_by(LeaderboardDaily.score.desc()).all()
        results = [{
            "rank": i+1,
            "username": User.query.get(e.user_id).username,
            "score": e.score
        } for i, e in enumerate(entries)]
    elif mode == 'progress':
        entries = LeaderboardProgress.query.order_by(LeaderboardProgress.avg_guesses.asc()).all()
        results = [{
            "rank": i+1,
            "username": User.query.get(e.user_id).username,
            "score": 0,
            "avgGuesses": e.avg_guesses
        } for i, e in enumerate(entries)]
    return jsonify(results)