from models import db, Lesson, Question, LearningQuestion

def seed_lessons():



    if Lesson.query.count() == 0:

        lesson1 = Lesson(
            lesson_number=1,
            title="Introduction to C",
            description="Learn the basics of C programming.",
            content="""
C is a powerful programming language.

It is used for:

• Operating Systems
• Embedded Systems
• Compilers
• Games

Example:

#include <stdio.h>

int main(){

printf("Hello World");

return 0;

}
"""
        )

        lesson2 = Lesson(
            lesson_number=2,
            title="Variables",
            description="Learn variables and data types.",
            content="Variables are used to store data."
        )

        lesson3 = Lesson(
            lesson_number=3,
            title="Input & Output",
            description="Learn scanf() and printf().",
            content="Input and Output in C."
        )

        db.session.add_all([lesson1, lesson2, lesson3])
        db.session.commit()

        # --------------------------
        # Questions for Lesson 1
        # --------------------------

        questions = [

            Question(
                lesson_id=lesson1.id,
                question="Who developed the C programming language?",
                option_a="Bjarne Stroustrup",
                option_b="Dennis Ritchie",
                option_c="James Gosling",
                option_d="Guido van Rossum",
                correct_answer="B",
                explanation="Dennis Ritchie developed C at Bell Labs."
            ),

            Question(
                lesson_id=lesson1.id,
                question="Which header file is required for printf()?",
                option_a="<stdio.h>",
                option_b="<math.h>",
                option_c="<string.h>",
                option_d="<stdlib.h>",
                correct_answer="A",
                explanation="printf() is declared in stdio.h."
            ),

            Question(
                lesson_id=lesson1.id,
                question="Which function is the entry point of every C program?",
                option_a="start()",
                option_b="main()",
                option_c="program()",
                option_d="run()",
                correct_answer="B",
                explanation="Execution of every C program begins with main()."
            ),

            Question(
                lesson_id=lesson1.id,
                question="Which symbol ends a statement in C?",
                option_a=":",
                option_b=",",
                option_c=";",
                option_d=".",
                correct_answer="C",
                explanation="Every statement in C ends with a semicolon."
            ),

            Question(
                lesson_id=lesson1.id,
                question="Which of these is NOT a use of C?",
                option_a="Operating Systems",
                option_b="Embedded Systems",
                option_c="Game Development",
                option_d="Photo Editing",
                correct_answer="D",
                explanation="Photo editing is not a direct application of C."
            )

        ]

        db.session.add_all(questions)
        db.session.commit()

        print("Questions in database:", Question.query.count())

        print("Lessons and Questions Added Successfully!")

def seed_learning_questions():

    if LearningQuestion.query.count() == 0:

        questions = [
            LearningQuestion(
                lesson_id=1,
                title="Hello World",
                difficulty="Easy",
                platform="HackerRank",
                problem_url="https://www.hackerrank.com/challenges/c-tutorial-hello-world"
            ),

            LearningQuestion(
                lesson_id=1,
                title="Basic Data Types",
                difficulty="Easy",
                platform="HackerRank",
                problem_url="https://www.hackerrank.com/challenges/c-tutorial-basic-data-types"
            ),

            LearningQuestion(
                lesson_id=1,
                title="For Loop",
                difficulty="Medium",
                platform="HackerRank",
                problem_url="https://www.hackerrank.com/challenges/c-tutorial-for-loop"
            )

        ]

        db.session.add_all(questions)
        db.session.commit()


from werkzeug.security import generate_password_hash
from models import Admin
def seed_admin():

    if Admin.query.first():
        print("Admin already exists")
        return

    admin = Admin(
        username="admin",
        password=generate_password_hash("admin123")
    )

    db.session.add(admin)
    db.session.commit()

    print("Admin created successfully")