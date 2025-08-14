import pandas as pd

def get_all_courses():
    df = pd.read_csv('data/courses.csv')
    return df['course'].tolist()

def get_course_details(course_name):
    df = pd.read_csv('data/courses.csv')
    for _, row in df.iterrows():
        if row['course'].strip().lower() == course_name.strip().lower():
            return f"{row['course']}: {row['description']}"
    return "Course not found."