# app/guesses/routes.py
from flask import Blueprint, jsonify, request
from .. import df_images
from ..models import User, LeaderboardDaily, LeaderboardProgress, LeaderboardCasual
from fuzzyset import FuzzySet
from .. import db
import datetime
import copy
guesses_bp = Blueprint('guesses', __name__)

def calculate_similarity(prompt, guess):
    '''
    
    return a tuple of (exact, similar, accuracy).
    exact: list of words that are exactly matched
    similar: list of tuples (guess_word, prompt_word) - words that are similar to the prompt
    accuracy: percentage of words that are matched
    score: based on accuracy and how hard the prompt is
    '''

    # filter pancuation marks from prompt and guess
    prompt = ''.join(e for e in prompt if e.isalnum() or e.isspace()).lower()
    guess = ''.join(e for e in guess if e.isalnum() or e.isspace()).lower()
    prompt_words = prompt.split()
    guess_words = guess.split()

    # exact_match = prompt_words == guess_words
    # if exact_match:
    #     return 100

    # if set(prompt_words).issubset(set(guess_words)):
    #     return 90

    
    round_matched = []
    final_matched = []
   
    round_matched = []
    fuzzy_prompt = FuzzySet(prompt_words)
    for word in guess_words:
        matches = fuzzy_prompt.get(word)
        if matches:
            round_matched += [(word, *m) for m in matches if m[0] >= 0.7]
            # current_guess_words.remove(word) # no point in going over it in the next round...

    # sort matched by highest match
    round_matched.sort(key=lambda x: x[1], reverse=True)
    # get found matches, avoid duplicate match entries. 
    current_guess_words = guess_words
    current_prompt_words = prompt_words.copy()
    for match in round_matched:
        if match[0] in current_guess_words and match[2] in current_prompt_words:
            final_matched.append(match)
            current_guess_words.remove(match[0])
            current_prompt_words.remove(match[2])
        else:
            continue
    
    # calculate final accuracy and make exact_matched abd similar_matched lists
    exact_matched = []
    similar_matched = []
    accuracy = 0
    score = 0
    for m in final_matched:
        if m[0] == m[2] :
            exact_matched.append(m[0])
        else:
            similar_matched.append((m[0], m[2]))
        accuracy += 1/len(prompt_words) * m[1] *100 # if all mathced this should be 100 
        score += m[1] * 100
    return exact_matched, similar_matched, accuracy, score
    
ACCURACY_THRESHOLD = 80
@guesses_bp.route('', methods=['POST'])
def submit_guess():
    data = request.get_json()
    image_id = data.get('imageId')
    guess = data.get('guess')
    mode = data.get('mode')
    level = data.get('level')
    userID = data.get('userId')
    print("user id - ", userID)
    image = df_images[df_images['id'] == image_id].iloc[0]
    exact_matched, similar_matched, accuracy, score = calculate_similarity(image['prompt'], guess)
    # @TODO: implement guest user in client 
    user_token = request.headers.get('Authorization', '').split(' ')[-1]
    print("user token is - ", user_token)
    if user_token not in ['guest', ''] and userID not in ['guest', None]:
        user = User.query.get(user_token)
        if mode == 'daily':
            if user.daily_score == None or user.daily_score < score:
                user.daily_score = score
            user.last_submission_date = datetime.datetime.now().date()
            daily_lb = LeaderboardDaily.query.get(user.token)
            daily_lb.score = user.daily_score
        elif mode == 'progress': 
            # update the user number of guesses
            # delete last entry which is tm
            del user.progress_levels[-1]

            level_info = next((lvl for lvl in user.progress_levels if lvl['level'] == level), None)
            # update the user progress levels
            level_info['guesses'] += 1
            print("[INFO] level info - ", level_info)
            if accuracy >= ACCURACY_THRESHOLD:
                if level_info:
                    print(f"[INFO] accuracy is greater than {ACCURACY_THRESHOLD}, updating level info")
                    level_info['completed'] += 1
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
            # force update of the user progress levels by adding and removing tmp
            user.progress_levels.append({"tmp" : 1})

        elif mode =='casual':
            # add score to casual scores and update casual leaderboard
            user.casual_score += score
            # update casual leaderboard
            casual_lb = LeaderboardCasual.query.get(user.token)
            casual_lb.score = user.casual_score

        db.session.commit()
    
    return jsonify({
        "originalPrompt": image['prompt'],
        "accuracy": accuracy,
        "score": score,
        "exactMatches": exact_matched,
        "similarMatches": similar_matched,
        "success": accuracy >= ACCURACY_THRESHOLD
    })