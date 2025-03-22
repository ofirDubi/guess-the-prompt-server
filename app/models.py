# app/models.py
from . import db
from datetime import datetime
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.dialects.postgresql import JSON

class User(db.Model):
    token = db.Column(db.String(36), primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    casual_score = db.Column(db.Integer, default=0)
    daily_score = db.Column(db.Integer, default=0)
    last_submission_date = db.Column(db.Date)
    progress_levels = db.Column(MutableList.as_mutable(JSON), default={})


class LeaderboardCasual(db.Model):
    user_id = db.Column(db.String(36), db.ForeignKey('user.token'), primary_key=True)
    score = db.Column(db.Integer, default=0)

class LeaderboardDaily(db.Model):
    user_id = db.Column(db.String(36), db.ForeignKey('user.token'), primary_key=True)
    score = db.Column(db.Integer, default=0)

class LeaderboardProgress(db.Model):
    user_id = db.Column(db.String(36), db.ForeignKey('user.token'), primary_key=True)
    avg_guesses = db.Column(db.Float, default=0.0)