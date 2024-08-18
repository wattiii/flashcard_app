import json
import os
import random
import streamlit as st
from PIL import Image
import hashlib

SETTINGS_FILE = 'settings.json'
USERS_FILE = 'users.json'


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as file:
            return json.load(file)
    return {"difficulty": "medium"}


def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as file:
        json.dump(settings, file)


def load_questions(filename):
    try:
        with open(filename, 'r') as file:
            questions = json.load(file)

        for question in questions:
            if 'image_path' in question and question['image_path']:
                try:
                    Image.open(question['image_path'])
                except:
                    st.warning(f"""Failed to load image for question {
                               question['id']}. The question will be displayed without an image.""")
                    question['image_path'] = None
            else:
                question['image_path'] = None

        return questions
    except (FileNotFoundError, json.JSONDecodeError):
        st.error(f"Error loading the file '{filename}'.")
        return []


def save_questions(filename, questions):
    with open(filename, 'w') as file:
        json.dump(questions, file, indent=2)


def initialize_quiz_state(questions, difficulty):
    ss = st.session_state
    num_questions = {"low": 10, "medium": 20, "hard": 30}[difficulty]
    ss.questions = random.sample(questions, min(num_questions, len(questions)))
    ss.total_questions = len(ss.questions)
    ss.correct_answers = 0
    ss.incorrect_questions = []
    ss.current_question = 0
    ss.shuffled_options = []
    for question in ss.questions:
        options = question['options'].copy()
        if question['correct_answer'] not in options:
            options.append(question['correct_answer'])
        random.shuffle(options)
        ss.shuffled_options.append(options)
    ss.quiz_started = False


def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as file:
            return json.load(file)
    return {}


def save_users(users):
    with open(USERS_FILE, 'w') as file:
        json.dump(users, file)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username, password):
    users = load_users()
    if username not in users:
        users[username] = hash_password(password)
        save_users(users)
        return True
    return False


def verify_user(username, password):
    users = load_users()
    return username in users and users[username] == hash_password(password)


def login():
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if verify_user(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.experimental_rerun()
        else:
            st.sidebar.error("Invalid username or password")


def create_account():
    st.sidebar.title("Create Account")
    new_username = st.sidebar.text_input("New Username")
    new_password = st.sidebar.text_input("New Password", type="password")
    if st.sidebar.button("Create Account"):
        if create_user(new_username, new_password):
            st.sidebar.success("Account created successfully!")
        else:
            st.sidebar.error("Username already exists")


def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.experimental_rerun()


def admin_interface(filename):
    st.title("Admin Interface")

    # Load questions at the start of the function
    questions = load_questions(filename)

    st.header("Create New Question")
    new_question = {}
    new_question['id'] = st.text_input("Question ID")
    new_question['question'] = st.text_area("Question Text")
    new_question['category'] = st.text_input("Category")
    new_question['difficulty'] = st.selectbox(
        "Difficulty", ["easy", "medium", "hard"])
    new_question['options'] = st.text_input(
        "Options (comma-separated)").split(',')
    new_question['correct_answer'] = st.text_input("Correct Answer")
    new_question['image_path'] = st.text_input("Image Path (optional)")

    if st.button("Add Question"):
        if new_question['id'] and new_question['question'] and new_question['options'] and new_question['correct_answer']:
            questions.append(new_question)
            save_questions(filename, questions)
            st.success("Question added successfully!")
        else:
            st.error("Please fill in all required fields.")

    st.header("Edit Existing Questions")
    questions_updated = False
    for i, question in enumerate(questions):
        st.subheader(f"Question {question['id']}")
        questions[i]['question'] = st.text_area(
            f"Question Text {i}", question['question'])
        questions[i]['category'] = st.text_input(
            f"Category {i}", question['category'])
        questions[i]['difficulty'] = st.selectbox(f"Difficulty {i}", ["easy", "medium", "hard"], [
                                                  "easy", "medium", "hard"].index(question['difficulty']))
        questions[i]['options'] = st.text_input(
            f"Options {i} (comma-separated)", ','.join(question['options'])).split(',')
        questions[i]['correct_answer'] = st.text_input(
            f"Correct Answer {i}", question['correct_answer'])
        questions[i]['image_path'] = st.text_input(
            f"Image Path {i} (optional)", question.get('image_path', ''))

        if st.button(f"Update Question {question['id']}"):
            questions_updated = True
            st.success(f"Question {question['id']} updated.")

        if st.button(f"Delete Question {question['id']}"):
            questions.pop(i)
            questions_updated = True
            st.success(f"Question {question['id']} deleted.")
            st.experimental_rerun()

    if questions_updated:
        save_questions(filename, questions)
        st.success("All changes saved successfully!")


def main():
    st.set_page_config(page_title="Interactive Quiz App",
                       page_icon="📚", layout="wide")

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login()
        create_account()
        return

    st.sidebar.title(f"Welcome, {st.session_state.username}!")
    if st.sidebar.button("Logout"):
        logout()

    json_files = [f for f in os.listdir() if f.endswith(
        '.json') and f not in [SETTINGS_FILE, USERS_FILE]]

    if not json_files:
        st.error("No question JSON files found in the current directory.")
        return

    filename = st.selectbox(
        """Select the JSON file with questions or log in as admin to write questions:""", json_files, key="file_selector")

    if not filename:
        st.write("Please select a JSON file to start.")
        return

    settings = load_settings()
    difficulty = st.selectbox("Select Difficulty:", ["low", "medium", "hard"],
                              index=["low", "medium", "hard"].index(
                                  settings["difficulty"]),
                              key="difficulty_selector")

    settings["difficulty"] = difficulty
    save_settings(settings)

    questions = load_questions(filename)

    if not questions:
        return

    if st.session_state.username == "admin":
        admin_interface(filename)
    else:
        quiz_interface(questions, difficulty, filename)


def quiz_interface(questions, difficulty, filename):
    if 'questions' not in st.session_state or \
       st.session_state.get('last_file') != filename or \
       st.session_state.get('last_difficulty') != difficulty:
        initialize_quiz_state(questions, difficulty)
        st.session_state.last_file = filename
        st.session_state.last_difficulty = difficulty

    ss = st.session_state

    if st.button("Start Quiz"):
        ss.quiz_started = True

    if ss.quiz_started:
        if ss.current_question < ss.total_questions:
            question = ss.questions[ss.current_question]
            st.write(f"**Question {question['id']}**: {question['question']}")

            if question['image_path']:
                try:
                    image = Image.open(question['image_path'])
                    st.image(image, caption=f"""Image for Question {
                             question['id']}""")
                except:
                    st.error(f"""Failed to display image for question {
                             question['id']}.""")

            options = ss.shuffled_options[ss.current_question]
            correct_answer = question['correct_answer']

            user_answer = st.radio("Choose:", options, key=f"""q_{
                                   ss.current_question}""")

            if st.button("Submit Answer", key=f"submit_{ss.current_question}"):
                if user_answer == correct_answer:
                    st.success("Correct!")
                    ss.correct_answers += 1
                else:
                    st.error(f"Incorrect! The answer is: {correct_answer}")
                    ss.incorrect_questions.append(question['id'])

                ss.current_question += 1
                st.experimental_rerun()

        else:
            st.write(f"""You answered {ss.correct_answers} out of {
                     ss.total_questions} questions correctly. Great job!""")

            if ss.incorrect_questions:
                st.write("You got the following questions wrong:")
                for q_id in ss.incorrect_questions:
                    st.write(f"  Question ID: {q_id}")

            if st.button("Restart Quiz"):
                initialize_quiz_state(questions, difficulty)
                st.experimental_rerun()


if __name__ == "__main__":
    main()
