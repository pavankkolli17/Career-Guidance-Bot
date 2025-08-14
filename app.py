from flask import Flask, render_template, request
import pandas as pd
from utils.career_search import search_career
from utils.course_info import get_courses
from utils.pathway_planner import get_pathway

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    response = None
    if request.method == 'POST':
        user_input = request.form['user_input'].strip().lower()
        if 'career' in user_input:
            response = search_career(user_input)
        elif 'course' in user_input:
            response = get_courses(user_input)
        elif 'pathway' in user_input:
            response = get_pathway(user_input)
        else:
            response = "Please ask about careers, courses, or pathways."
    return render_template('index.html', response=response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
