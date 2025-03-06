# app/guesses/routes.py
from flask import Blueprint, jsonify, request
from .. import df_images
from ..models import User, LeaderboardDaily, LeaderboardProgress
from fuzzyset import FuzzySet
from .. import db

guesses_bp = Blueprint('guesses', __name__)

def calculate_similarity(prompt, guess):
    prompt_words = prompt.split()
    guess_words = guess.split()

    exact_match = prompt_words == guess_words
    if exact_match:
        return 100

    if set(prompt_words).issubset(set(guess_words)):
        return 90

    fuzzy_guess = FuzzySet(guess_words)
    matched = []
    for word in prompt_words:
        matches = fuzzy_guess.get(word)
        if matches and matches[0][0] >= 0.8:
            matched.append(matches[0][1])
    
    return round((len(set(matched)) / len(prompt_words)) * 100)

@guesses_bp.route('', methods=['POST'])
def submit_guess():
    data = request.get_json()
    image_id = data.get('imageId')
    guess = data.get('guess')
    mode = data.get('mode')
    level = data.get('level')
    userID = data.get('userID')
    print("user id - ", userID)
    image = df_images[df_images['id'] == image_id].iloc[0]
    similarity = calculate_similarity(image['prompt'], guess)
    # @TODO: implement guest user in client 
    user_token = request.headers.get('Authorization', '').split(' ')[-1]
    print("user token is - ", user_token)
    if user_token != 'guest':
        user = User.query.get(user_token)
        if mode == 'daily':
            user.daily_score += similarity
            user.last_submission_date = datetime.now().date()
            daily_lb = LeaderboardDaily.query.get(user.token)
            daily_lb.score = user.daily_score
        elif mode == 'progress' and similarity >= 80:
            level_info = next((lvl for lvl in user.progress_levels if lvl['level'] == level), None)
            if level_info:
                level_info['completed'] += 1
                level_info['guesses'] += 1
                if level_info['completed'] >= level_info['total']:
                    new_level = level + 1
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
        "originalPrompt": image['prompt'],
        "similarity": similarity,
        "score": similarity,
        "exactMatches": image['prompt'].split() if similarity >= 90 else [],
        "similarMatches": list(set(guess.split()) - set(image['prompt'].split())) if similarity < 90 else [],
        "success": similarity >= 80
    })