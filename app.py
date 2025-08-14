from flask import Flask, request, jsonify
from utils.career_search import get_all_careers, get_career_details
from utils.course_search import get_all_courses, get_course_details

app = Flask(__name__)

# This will hold temporary state for user sessions (simple approach)
user_states = {}

@app.route('/chat', methods=['POST'])
def chat():
    user_id = request.json.get('user_id', 'default')
    user_input = request.json.get('message', '').strip().lower()

    # If no state exists for this user, create one
    if user_id not in user_states:
        user_states[user_id] = {"mode": None}

    state = user_states[user_id]

    # Step 1: Detect if user is asking about careers or courses
    if state["mode"] is None:
        if "career" in user_input:
            state["mode"] = "career_list"
            careers = get_all_careers()
            return jsonify({"response": "Here are available careers. Please type the career name to know more:",
                            "options": careers})

        elif "course" in user_input:
            state["mode"] = "course_list"
            courses = get_all_courses()
            return jsonify({"response": "Here are available courses. Please type the course name to know more:",
                            "options": courses})

        else:
            return jsonify({"response": "Please start by typing 'career' or 'course'."})

    # Step 2: If user has chosen a career
    elif state["mode"] == "career_list":
        details = get_career_details(user_input)
        state["mode"] = None  # Reset state
        return jsonify({"response": details})

    # Step 3: If user has chosen a course
    elif state["mode"] == "course_list":
        details = get_course_details(user_input)
        state["mode"] = None  # Reset state
        return jsonify({"response": details})

    return jsonify({"response": "Something went wrong."})


if __name__ == '__main__':
    app.run(debug=True)