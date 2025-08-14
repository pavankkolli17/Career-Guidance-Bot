import pandas as pd

def get_all_careers():
    df = pd.read_csv('data/careers.csv')
    df = df.dropna(subset=['career'])  # remove rows where 'career' is empty
    return [c.strip() for c in df['career'].tolist()]

def get_career_details(query):
    df = pd.read_csv('data/careers.csv')
    df = df.dropna(subset=['career'])
    for _, row in df.iterrows():
        if row['career'].strip().lower() == query.lower():
            return f"{row['career']}: {row['description']}"
    return "Career not found."
