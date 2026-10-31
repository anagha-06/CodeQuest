from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(50), unique=True, nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)

    points = db.Column(db.Integer, default=0)

    current_streak = db.Column(db.Integer, default=0)

    highest_streak = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    last_login = db.Column(db.DateTime)


class Lesson(db.Model):
    __tablename__ = "lessons"

    id = db.Column(db.Integer, primary_key=True)

    lesson_number = db.Column(db.Integer, unique=True)

    title = db.Column(db.String(200))

    description = db.Column(db.String(300))

    content = db.Column(db.Text)


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)

    lesson_id = db.Column(
        db.Integer,
        db.ForeignKey("lessons.id")
    )

    question = db.Column(db.Text)

    option_a = db.Column(db.String(200))
    option_b = db.Column(db.String(200))
    option_c = db.Column(db.String(200))
    option_d = db.Column(db.String(200))

    correct_answer = db.Column(db.String(1))

    explanation = db.Column(db.Text)

class Progress(db.Model):
    __tablename__ = "progress"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")   # or "user.id" depending on your User model
    )

    lesson_id = db.Column(
        db.Integer,
        db.ForeignKey("lessons.id")
    )

    attempts = db.Column(db.Integer, default=0)

    score = db.Column(db.Integer)

    percentage = db.Column(db.Integer)

    completed = db.Column(db.Boolean, default=False)
    
class LearningQuestion(db.Model):
    __tablename__ = "learning_questions"

    id = db.Column(db.Integer, primary_key=True)

    lesson_id = db.Column(
        db.Integer,
        db.ForeignKey("lessons.id")
    )

    title = db.Column(db.String(200), nullable=False)

    difficulty = db.Column(db.String(20), nullable=False)

    platform = db.Column(db.String(30), nullable=False)

    problem_url = db.Column(db.String(500), nullable=False)

class PracticeProgress(db.Model):
    __tablename__ = "practice_progress"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    question_id = db.Column(
        db.Integer,
        db.ForeignKey("learning_questions.id"),
        nullable=False
    )
    completed = db.Column(
        db.Boolean,
        default=False
    )

class Admin(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )