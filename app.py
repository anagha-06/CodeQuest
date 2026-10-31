from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps

from config import Config
from models import db, User, Lesson, Question, Progress, LearningQuestion, PracticeProgress, Admin
from seed import seed_lessons, seed_learning_questions, seed_admin
from datetime import datetime, timedelta

app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

with app.app_context():
    db.create_all()
    seed_lessons()
    seed_learning_questions()
    seed_admin()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



# ------------------------
# Admin Login Required
# ------------------------

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        admin_id = session.get("admin")

        if not admin_id or not db.session.get(Admin, admin_id):
            session.pop("admin", None)
            flash("Please login as admin.", "warning")
            return redirect(url_for("admin_login"))

        return f(*args, **kwargs)

    return decorated_function

def update_streak(user):

    today = datetime.utcnow().date()

    if user.last_login is None:
        user.current_streak = 1

    else:

        last_date = user.last_login.date()

        if last_date == today:
            return

        elif last_date == today - timedelta(days=1):
            user.current_streak += 1

        else:
            user.current_streak = 1

    if user.current_streak > user.highest_streak:
        user.highest_streak = user.current_streak

    user.last_login = datetime.utcnow()

    db.session.commit()

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash("Username already exists!", "danger")
            return redirect(url_for("register"))

        # Create new user
        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration Successful! Please Login.", "success")

        return redirect(url_for("home"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):

            login_user(user)
            
            update_streak(user)
            
            flash("Welcome back!", "success")
            
            return redirect(url_for("dashboard"))

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged out successfully.", "success")

    return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():

    completed = Progress.query.filter_by(
        user_id=current_user.id,
        completed=True
    ).count()

    total_lessons = Lesson.query.count()

    progress_percentage = 0

    if total_lessons > 0:
        progress_percentage = int((completed / total_lessons) * 100)

    return render_template(
        "dashboard.html",
        user=current_user,
        completed=completed,
        total_lessons=total_lessons,
        progress_percentage=progress_percentage
    )

@app.route("/leaderboard")
@login_required
def leaderboard():

    users = User.query.order_by(User.points.desc()).all()

    return render_template(
        "leaderboard.html",
        users=users
    )


@app.route("/lessons")
@login_required
def lessons():


    all_lessons = Lesson.query.order_by(Lesson.lesson_number).all()

    progress = Progress.query.filter_by(
        user_id=current_user.id
    ).all()

    completed_lessons = []

    for p in progress:
        if p.completed:
            completed_lessons.append(p.lesson_id)

    return render_template(
        "lessons.html",
        lessons=all_lessons,
        completed_lessons=completed_lessons
    )

@app.route("/lesson/<int:lesson_id>")
@login_required
def lesson(lesson_id):

    lesson = Lesson.query.get_or_404(lesson_id)

    return render_template(
        "lesson.html",
        lesson=lesson
    )

@app.route("/quiz/<int:lesson_id>", methods=["GET", "POST"])
@login_required

def quiz(lesson_id):

    lesson = Lesson.query.get_or_404(lesson_id)
    questions = Question.query.filter_by(lesson_id=lesson_id).all()

    progress = Progress.query.filter_by(
        user_id=current_user.id,
        lesson_id=lesson.id
    ).first()
    if progress and progress.completed:
        flash(
            "✅ You have already completed this quiz. Retaking is not allowed.",
            "info"
        )
        return redirect(url_for("lesson", lesson_id=lesson.id))


    '''print("\n==============================")
    print("Lesson ID:", lesson_id)
    print("Lesson:", lesson.title)
    print("Questions Found:", len(questions))

    for q in questions:
        print(q.lesson_id, q.question)

    print("==============================\n")'''

    if request.method == "POST":

        score = 0
        results = []

        for question in questions:

            selected = request.form.get(f"question{question.id}")

            correct = selected == question.correct_answer

            if correct:
                score += 1

            results.append({
                "question": question.question,
                "selected": selected,
                "correct_answer": question.correct_answer,
                "option_a": question.option_a,
                "option_b": question.option_b,
                "option_c": question.option_c,
                "option_d": question.option_d,
                "correct": correct,
                "explanation": question.explanation
            })

        percentage = round(score / len(questions) * 100)
        progress = Progress.query.filter_by(
            user_id=current_user.id,
            lesson_id=lesson.id
            ).first()
        if not progress:
            progress = Progress(
                user_id=current_user.id,
                lesson_id=lesson.id,
                attempts=0
                )
        db.session.add(progress)
        attempt_number = progress.attempts + 1
        progress.attempts = attempt_number
        progress.score = score
        progress.percentage = percentage
        if percentage >= 80:
            progress.completed = True
            if attempt_number == 1:
                current_user.points += 100
            else:
                current_user.points += 80
        else:
            progress.completed = False
            if attempt_number == 1:
                current_user.points += 20
        db.session.commit()

        '''progress = Progress.query.filter_by(
            user_id=current_user.id,
            lesson_id=lesson.id
        ).first()
        if not progress:
            progress = Progress(
                user_id=current_user.id,
                lesson_id=lesson.id
            )
        progress.score = score
        progress.percentage = percentage
        progress.completed = percentage >= 80
        db.session.add(progress)
        db.session.commit()'''

        next_lesson = Lesson.query.filter_by(
            lesson_number=lesson.lesson_number + 1
        ).first()

        return render_template(
            "result.html",
            lesson=lesson,
            score=score,
            total=len(questions),
            percentage=percentage,
            results=results,
            next_lesson=next_lesson
        )

    return render_template(
        "quiz.html",
        lesson=lesson,
        questions=questions
    )

@app.route("/arena")
@login_required
def arena():

    lessons = Lesson.query.order_by(
        Lesson.lesson_number
    ).all()

    return render_template(
        "arena.html",
        lessons=lessons
    )

@app.route("/arena/<int:lesson_id>")
@login_required
def arena_lesson(lesson_id):

    lesson = Lesson.query.get_or_404(lesson_id)
    questions = LearningQuestion.query.filter_by(
        lesson_id=lesson.id
    ).all()
    
    completed_questions = {
        
        progress.question_id
        for progress in PracticeProgress.query.filter_by(
            user_id=current_user.id,
            completed=True
        ).all()
    }

    return render_template(
    "arena_lesson.html",
    lesson=lesson,
    questions=questions,
    completed_questions=completed_questions
    )

@app.route("/practice_complete/<int:question_id>")
@login_required
def practice_complete(question_id):

    progress = PracticeProgress.query.filter_by(
        user_id=current_user.id,
        question_id=question_id
    ).first()

    if not progress:

        progress = PracticeProgress(
            user_id=current_user.id,
            question_id=question_id,
            completed=True
        )

        db.session.add(progress)

    else:

        progress.completed = True

    db.session.commit()

    flash(
        "Question marked as completed!",
        "success"
    )

    question = LearningQuestion.query.get_or_404(question_id)

    return redirect(
        url_for(
            "arena_lesson",
            lesson_id=question.lesson_id
        )
    )

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        admin = Admin.query.filter_by(username=username).first()

        if admin and check_password_hash(admin.password, password):
            session["admin"] = admin.id
            flash("Welcome, Admin!", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin credentials", "danger")

    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():

    session.pop("admin", None)

    return redirect(url_for("admin_login"))

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():

    total_users = User.query.count()
    total_lessons = Lesson.query.count()
    total_quiz_questions = Question.query.count()
    total_practice_questions = LearningQuestion.query.count()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_lessons=total_lessons,
        total_quiz_questions=total_quiz_questions,
        total_practice_questions=total_practice_questions
    )

@app.route("/admin/lessons")
@admin_required
def manage_lessons():

    lessons = Lesson.query.order_by(
        Lesson.lesson_number
    ).all()

    return render_template(
        "manage_lessons.html",
        lessons=lessons
    )

@app.route("/admin/lessons/add", methods=["GET", "POST"])
@admin_required
def add_lesson():

    if request.method == "POST":

        lesson_number = request.form["lesson_number"].strip()
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        content = request.form["content"].strip()

        if not lesson_number.isdigit() or int(lesson_number) < 1:
            flash("Please enter a valid positive lesson number.", "danger")
            return redirect(url_for("add_lesson"))

        lesson_number = int(lesson_number)

        existing_lesson = Lesson.query.filter_by(
            lesson_number=lesson_number
        ).first()

        if existing_lesson:
            flash("A lesson with this number already exists.", "danger")
            return redirect(url_for("add_lesson"))

        new_lesson = Lesson(
            lesson_number=lesson_number,
            title=title,
            description=description,
            content=content
        )

        db.session.add(new_lesson)
        db.session.commit()

        flash("Lesson added successfully!", "success")

        return redirect(url_for("manage_lessons"))

    return render_template("add_lesson.html")

@app.route("/admin/lessons/edit/<int:lesson_id>", methods=["GET", "POST"])
@admin_required
def edit_lesson(lesson_id):

    lesson = Lesson.query.get_or_404(lesson_id)

    if request.method == "POST":

        lesson_number = request.form["lesson_number"].strip()

        if not lesson_number.isdigit() or int(lesson_number) < 1:
            flash("Please enter a valid positive lesson number.", "danger")
            return redirect(url_for("edit_lesson", lesson_id=lesson.id))

        lesson_number = int(lesson_number)

        existing_lesson = Lesson.query.filter(
            Lesson.lesson_number == lesson_number,
            Lesson.id != lesson.id
        ).first()

        if existing_lesson:
            flash("Another lesson already uses this number.", "danger")
            return redirect(url_for("edit_lesson", lesson_id=lesson.id))

        lesson.lesson_number = lesson_number
        lesson.title = request.form["title"].strip()
        lesson.description = request.form["description"].strip()
        lesson.content = request.form["content"].strip()

        db.session.commit()

        flash("Lesson updated successfully!", "success")

        return redirect(url_for("manage_lessons"))

    return render_template(
        "edit_lesson.html",
        lesson=lesson
    )


@app.route("/admin/lessons/delete/<int:lesson_id>", methods=["POST"])
@admin_required
def delete_lesson(lesson_id):

    lesson = Lesson.query.get_or_404(lesson_id)

    existing_progress = Progress.query.filter_by(
        lesson_id=lesson.id
    ).first()

    if existing_progress:
        flash(
            "This lesson has student progress and cannot be deleted.",
            "warning"
        )
        return redirect(url_for("manage_lessons"))

    practice_questions = LearningQuestion.query.filter_by(
        lesson_id=lesson.id
    ).all()

    for question in practice_questions:

        PracticeProgress.query.filter_by(
            question_id=question.id
        ).delete()

        db.session.delete(question)

    Question.query.filter_by(
        lesson_id=lesson.id
    ).delete()

    db.session.delete(lesson)
    db.session.commit()

    flash("Lesson deleted successfully!", "success")

    return redirect(url_for("manage_lessons"))

@app.route("/admin/questions")
@admin_required
def manage_questions():

    questions = (
        db.session.query(Question, Lesson)
        .join(Lesson, Question.lesson_id == Lesson.id)
        .order_by(Lesson.lesson_number, Question.id)
        .all()
    )

    return render_template(
        "manage_questions.html",
        questions=questions
    )

@app.route("/admin/questions/add", methods=["GET", "POST"])
@admin_required
def add_question():

    lessons = Lesson.query.order_by(
        Lesson.lesson_number
    ).all()

    if not lessons:
        flash("Please add a lesson before adding quiz questions.", "warning")
        return redirect(url_for("manage_questions"))

    if request.method == "POST":

        lesson_id = request.form.get("lesson_id", type=int)

        lesson = db.session.get(Lesson, lesson_id) if lesson_id else None

        if not lesson:
            flash("Please select a valid lesson.", "danger")
            return redirect(url_for("add_question"))

        question_text = request.form["question"].strip()
        option_a = request.form["option_a"].strip()
        option_b = request.form["option_b"].strip()
        option_c = request.form["option_c"].strip()
        option_d = request.form["option_d"].strip()
        correct_answer = request.form["correct_answer"]
        explanation = request.form["explanation"].strip()

        if not all([
            question_text, option_a, option_b,
            option_c, option_d
        ]):
            flash("Please fill in all question and option fields.", "danger")
            return redirect(url_for("add_question"))

        if correct_answer not in ["A", "B", "C", "D"]:
            flash("Please select a valid correct answer.", "danger")
            return redirect(url_for("add_question"))

        new_question = Question(
            lesson_id=lesson.id,
            question=question_text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_answer=correct_answer,
            explanation=explanation
        )

        db.session.add(new_question)
        db.session.commit()

        flash("Quiz question added successfully!", "success")

        return redirect(url_for("manage_questions"))

    return render_template(
        "add_question.html",
        lessons=lessons
    )

@app.route("/admin/questions/edit/<int:question_id>", methods=["GET", "POST"])
@admin_required
def edit_question(question_id):

    question = Question.query.get_or_404(question_id)

    lessons = Lesson.query.order_by(
        Lesson.lesson_number
    ).all()

    if request.method == "POST":

        lesson_id = request.form.get("lesson_id", type=int)
        lesson = db.session.get(Lesson, lesson_id) if lesson_id else None

        if not lesson:
            flash("Please select a valid lesson.", "danger")
            return redirect(url_for("edit_question", question_id=question.id))

        correct_answer = request.form["correct_answer"]

        if correct_answer not in ["A", "B", "C", "D"]:
            flash("Please select a valid correct answer.", "danger")
            return redirect(url_for("edit_question", question_id=question.id))

        question_text = request.form["question"].strip()
        option_a = request.form["option_a"].strip()
        option_b = request.form["option_b"].strip()
        option_c = request.form["option_c"].strip()
        option_d = request.form["option_d"].strip()

        if not all([
            question_text, option_a, option_b,
            option_c, option_d
        ]):
            flash("Please fill in all question and option fields.", "danger")
            return redirect(url_for("edit_question", question_id=question.id))

        question.lesson_id = lesson.id
        question.question = question_text
        question.option_a = option_a
        question.option_b = option_b
        question.option_c = option_c
        question.option_d = option_d
        question.correct_answer = correct_answer
        question.explanation = request.form["explanation"].strip()

        db.session.commit()

        flash("Quiz question updated successfully!", "success")

        return redirect(url_for("manage_questions"))

    return render_template(
        "edit_question.html",
        question=question,
        lessons=lessons
    )

@app.route("/admin/questions/delete/<int:question_id>", methods=["POST"])
@admin_required
def delete_question(question_id):

    question = Question.query.get_or_404(question_id)

    db.session.delete(question)
    db.session.commit()

    flash("Quiz question deleted successfully!", "success")

    return redirect(url_for("manage_questions"))

@app.route("/admin/practice")
@admin_required
def manage_practice():

    questions = (
        db.session.query(LearningQuestion, Lesson)
        .join(Lesson, LearningQuestion.lesson_id == Lesson.id)
        .order_by(Lesson.lesson_number, LearningQuestion.id)
        .all()
    )

    return render_template(
        "manage_practice.html",
        questions=questions
    )

@app.route("/admin/practice/add", methods=["GET", "POST"])
@admin_required
def add_practice():

    lessons = Lesson.query.order_by(
        Lesson.lesson_number
    ).all()

    if not lessons:
        flash("Please add a lesson first.", "warning")
        return redirect(url_for("manage_practice"))

    if request.method == "POST":

        lesson_id = request.form.get("lesson_id", type=int)
        lesson = db.session.get(Lesson, lesson_id) if lesson_id else None

        if not lesson:
            flash("Please select a valid lesson.", "danger")
            return redirect(url_for("add_practice"))

        title = request.form["title"].strip()
        difficulty = request.form["difficulty"]
        platform = request.form["platform"].strip()
        problem_url = request.form["problem_url"].strip()

        if not all([title, difficulty, platform, problem_url]):
            flash("Please fill in all fields.", "danger")
            return redirect(url_for("add_practice"))

        if difficulty not in ["Easy", "Medium", "Hard"]:
            flash("Please select a valid difficulty.", "danger")
            return redirect(url_for("add_practice"))

        if not problem_url.startswith(("https://", "http://")):
            flash("Please enter a valid HTTP or HTTPS problem URL.", "danger")
            return redirect(url_for("add_practice"))

        new_question = LearningQuestion(
            lesson_id=lesson.id,
            title=title,
            difficulty=difficulty,
            platform=platform,
            problem_url=problem_url
        )

        db.session.add(new_question)
        db.session.commit()

        flash("Practice question added successfully!", "success")

        return redirect(url_for("manage_practice"))

    return render_template(
        "add_practice.html",
        lessons=lessons
    )

@app.route("/admin/practice/edit/<int:question_id>", methods=["GET", "POST"])
@admin_required
def edit_practice(question_id):

    question = LearningQuestion.query.get_or_404(question_id)

    lessons = Lesson.query.order_by(
        Lesson.lesson_number
    ).all()

    if request.method == "POST":

        lesson_id = request.form.get("lesson_id", type=int)
        lesson = db.session.get(Lesson, lesson_id) if lesson_id else None

        if not lesson:
            flash("Please select a valid lesson.", "danger")
            return redirect(url_for("edit_practice", question_id=question.id))

        title = request.form["title"].strip()
        difficulty = request.form["difficulty"]
        platform = request.form["platform"].strip()
        problem_url = request.form["problem_url"].strip()

        if not all([title, difficulty, platform, problem_url]):
            flash("Please fill in all fields.", "danger")
            return redirect(url_for("edit_practice", question_id=question.id))

        if difficulty not in ["Easy", "Medium", "Hard"]:
            flash("Please select a valid difficulty.", "danger")
            return redirect(url_for("edit_practice", question_id=question.id))

        if not problem_url.startswith(("https://", "http://")):
            flash("Please enter a valid HTTP or HTTPS problem URL.", "danger")
            return redirect(url_for("edit_practice", question_id=question.id))

        question.lesson_id = lesson.id
        question.title = title
        question.difficulty = difficulty
        question.platform = platform
        question.problem_url = problem_url

        db.session.commit()

        flash("Practice question updated successfully!", "success")

        return redirect(url_for("manage_practice"))

    return render_template(
        "edit_practice.html",
        question=question,
        lessons=lessons
    )

@app.route("/admin/practice/delete/<int:question_id>", methods=["POST"])
@admin_required
def delete_practice(question_id):

    question = LearningQuestion.query.get_or_404(question_id)

    PracticeProgress.query.filter_by(
        question_id=question.id
    ).delete()

    db.session.delete(question)
    db.session.commit()

    flash("Practice question deleted successfully!", "success")

    return redirect(url_for("manage_practice"))

@app.route("/admin/students")
@admin_required
def view_students():

    students = User.query.order_by(User.username).all()

    total_lessons = Lesson.query.count()

    student_data = []

    for student in students:

        # Count completed lessons
        completed_lessons = Progress.query.filter_by(
            user_id=student.id,
            completed=True
        ).count()

        # Count completed practice questions
        completed_practice = PracticeProgress.query.filter_by(
            user_id=student.id,
            completed=True
        ).count()

        student_data.append({
            "student": student,
            "completed_lessons": completed_lessons,
            "completed_practice": completed_practice
        })

    return render_template(
        "view_students.html",
        student_data=student_data,
        total_lessons=total_lessons
    )


if __name__ == "__main__":
    app.run(debug=True)