from flask import Flask, request, jsonify, render_template
from utils.career_search import get_all_careers, get_career_details
from utils.course_search import get_all_courses, get_course_details

app = Flask(__name__)

user_states = {}

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data:
        return jsonify({"response": "Please send JSON with 'user_id' and 'message'"}), 400

    user_id = data.get('user_id', 'default')
    user_input = data.get('message', '').strip().lower()

    if user_id not in user_states:
        user_states[user_id] = {"mode": None}

    state = user_states[user_id]

    if state["mode"] is None:
        if "career" in user_input:
            state["mode"] = "career_list"
            careers = get_all_careers()
            return jsonify({
                "response": "Here are available careers. Please click one to know more:",
                "options": careers
            })
        elif "course" in user_input:
            state["mode"] = "course_list"
            courses = get_all_courses()
            return jsonify({
                "response": "Here are available courses. Please click one to know more:",
                "options": courses
            })
        else:
            return jsonify({"response": "Please start by typing 'career' or 'course'."})
    elif state["mode"] == "career_list":
        details = get_career_details(user_input)
        state["mode"] = None
        return jsonify({"response": details})
    elif state["mode"] == "course_list":
        details = get_course_details(user_input)
        state["mode"] = None
        return jsonify({"response": details})

    return jsonify({"response": "Something went wrong."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)