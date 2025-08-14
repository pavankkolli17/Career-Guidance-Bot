import pandas as pd

def get_courses(query):
    df = pd.read_csv('data/courses.csv')
    results = []
    for _, row in df.iterrows():
        if row['career'].lower() in query or row['course'].lower() in query:
            results.append(f"{row['course']}: {row['description']}")
    return " | ".join(results) if results else "No courses found."
