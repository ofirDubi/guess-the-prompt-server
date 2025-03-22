import pandas as pd
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from fuzzyset import FuzzySet
import uuid
import bcrypt
from datetime import datetime
from waitress import serve

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///guess_the_prompt.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Load image data
df_images = pd.read_csv('data/selected_images/selected_images.csv')

class User(db.Model):
    token = db.Column(db.String(36), primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    casual_score = db.Column(db.Integer, default=0)
    daily_score = db.Column(db.Integer, default=0)
    progress_levels = db.Column(db.JSON)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.progress_levels:
            self.progress_levels = [{
                "level": 1,
                "completed": 0,
                "total": 10,
                "guesses": 0,
                "unlocked": True
            }]

class LeaderboardCasual(db.Model):
    user_id = db.Column(db.String(36), db.ForeignKey('user.token'), primary_key=True)
    score = db.Column(db.Integer, default=0)

class LeaderboardDaily(db.Model):
    user_id = db.Column(db.String(36), db.ForeignKey('user.token'), primary_key=True)
    score = db.Column(db.Integer, default=0)

class LeaderboardProgress(db.Model):
    user_id = db.Column(db.String(36), db.ForeignKey('user.token'), primary_key=True)
    avg_guesses = db.Column(db.Float, default=0.0)

@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password_hash = data.get('password')
    print("[+] registration data - ", data)
    if User.query.filter_by(username=username).first():
        return jsonify({"error": True, "message": "Username already exists", "code": 400}), 400

    token = str(uuid.uuid4())
    new_user = User(
        token=token,
        username=username,
        password_hash=password_hash
    )
    
    db.session.add(new_user)
    db.session.add(LeaderboardCasual(user_id=token))
    db.session.add(LeaderboardDaily(user_id=token))
    db.session.add(LeaderboardProgress(user_id=token))
    db.session.commit()

    return jsonify({
        "id": token,
        "username": username,
        "casualScore": 0,
        "dailyScore": 0,
        "token": token,
        "progressLevels": new_user.progress_levels
    }), 201

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password_hash = data.get('password')

    user = User.query.filter_by(username=username).first()
    if not user or user.password_hash != password_hash:
        return jsonify({"error": True, "message": "Invalid credentials", "code": 401}), 401

    return jsonify({
        "id": user.token,
        "username": user.username,
        "casualScore": user.casual_score,
        "dailyScore": user.daily_score,
        "token": user.token,
        "progressLevels": user.progress_levels
    }), 200

@app.route('/images/random', methods=['GET'])
def get_random_image():
    image = df_images.sample().iloc[0]
    return jsonify({
        "id": image['id'],
        "imageUrl": image['image_url'], # image url should be the place on the server where the image is stored.
        # should i give users access to it? probably not because then they can count on the images... but NVM for now
        "promptLength": len(image['prompt'].split())
    })

@app.route('/images/daily', methods=['GET'])
def get_daily_image():
    today = datetime.now().date()
    daily_image = df_images[df_images['type'] == 'daily'].sample(
        random_state=int(today.toordinal())
    ).iloc[0]
    
    user_token = request.headers.get('Authorization', '').split(' ')[-1] if request.headers.get('Authorization') else None
    has_submitted = False
    if user_token:
        user = User.query.get(user_token)
        # Implement daily submission tracking logic here
    
    return jsonify({
        "id": daily_image['id'],
        "imageUrl": daily_image['image_url'],
        "promptLength": len(daily_image['prompt'].split()),
        "hasSubmittedToday": has_submitted
    })

@app.route('/images/progress/<int:level>', methods=['GET'])
def get_progress_image(level):
    user_token = request.headers.get('Authorization', '').split(' ')[-1]
    user = User.query.get(user_token)
    
    if not user:
        return jsonify({"error": True, "message": "User not found", "code": 404}), 404

    level_info = next((lvl for lvl in user.progress_levels if lvl['level'] == level), None)
    if not level_info or not level_info['unlocked']:
        return jsonify({"error": True, "message": "Level not unlocked", "code": 403}), 403

    image_number = level_info['completed'] + 1
    image = df_images[
        (df_images['level'] == level) & 
        (df_images['image_number'] == image_number)
    ].iloc[0]

    return jsonify({
        "id": image['id'],
        "imageUrl": image['image_url'],
        "promptLength": len(image['prompt'].split()),
        "level": level,
        "imageNumber": image_number,
        "totalImagesInLevel": level_info['total']
    })

@app.route('/guess', methods=['POST'])
def submit_guess():
    data = request.get_json()
    image_id = data.get('imageId')
    guess = data.get('guess')
    mode = data.get('mode')
    level = data.get('level')

    image = df_images[df_images['id'] == image_id].iloc[0]
    prompt_words = image['prompt'].split()
    guess_words = guess.split()

    # Calculate similarity
    exact_match = prompt_words == guess_words
    if exact_match:
        similarity = 100
    else:
        prompt_set = set(prompt_words)
        guess_set = set(guess_words)
        if prompt_set.issubset(guess_set):
            similarity = 90
        else:
            fuzzy_guess = FuzzySet(guess_words)
            matched = []
            for word in prompt_words:
                matches = fuzzy_guess.get(word)
                if matches and matches[0][0] >= 0.8:
                    matched.append(matches[0][1])
            similarity = round((len(set(matched)) / len(prompt_words)) * 100)

    # Update user data if authenticated
    user_token = request.headers.get('Authorization', '').split(' ')[-1]
    if user_token and mode != 'casual':
        user = User.query.get(user_token)
        if mode == 'daily':
            user.daily_score += similarity
            leaderboard = LeaderboardDaily.query.get(user.token)
            leaderboard.score = user.daily_score
        elif mode == 'progress' and similarity >= 80:
            level_info = next((lvl for lvl in user.progress_levels if lvl['level'] == level), None)
            if level_info:
                level_info['completed'] += 1
                level_info['guesses'] += 1
                if level_info['completed'] >= level_info['total']:
                    next_level = level + 1
                    if not any(l['level'] == next_level for l in user.progress_levels):
                        user.progress_levels.append({
                            "level": next_level,
                            "completed": 0,
                            "total": 10,
                            "guesses": 0,
                            "unlocked": True
                        })
                # Update progress leaderboard
                total_guesses = sum(l['guesses'] for l in user.progress_levels if l['completed'])
                avg_guesses = total_guesses / len(user.progress_levels) if user.progress_levels else 0
                progress_lb = LeaderboardProgress.query.get(user.token)
                progress_lb.avg_guesses = avg_guesses
        db.session.commit()

    return jsonify({
        "originalPrompt": image['prompt'],
        "similarity": similarity,
        "score": similarity,
        "exactMatches": prompt_words if similarity >= 90 else [],
        "similarMatches": list(set(guess_words) - set(prompt_words)) if similarity < 90 else [],
        "success": similarity >= 80
    })

@app.route('/progress/complete', methods=['POST'])
def complete_level():
    data = request.get_json()
    level = data.get('level')
    guesses = data.get('guesses')
    
    user_token = request.headers.get('Authorization', '').split(' ')[-1]
    user = User.query.get(user_token)
    
    level_info = next((lvl for lvl in user.progress_levels if lvl['level'] == level), None)
    level_info['guesses'] = guesses
    level_info['completed'] = level_info['total']
    
    next_level = level + 1
    if not any(l['level'] == next_level for l in user.progress_levels):
        user.progress_levels.append({
            "level": next_level,
            "completed": 0,
            "total": 10,
            "guesses": 0,
            "unlocked": True
        })
    
    # Update progress leaderboard
    total_guesses = sum(l['guesses'] for l in user.progress_levels if l['completed'])
    avg_guesses = total_guesses / len(user.progress_levels) if user.progress_levels else 0
    progress_lb = LeaderboardProgress.query.get(user.token)
    progress_lb.avg_guesses = avg_guesses
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "nextLevel": next_level,
        "unlocked": True
    })

@app.route('/leaderboard/<string:mode>', methods=['GET'])
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    serve(app, host='0.0.0.0', port=3000)