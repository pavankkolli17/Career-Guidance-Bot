import pandas as pd

def search_career(query):
    df = pd.read_csv('data/careers.csv')
    for _, row in df.iterrows():
        if row['career'].lower() in query:
            return f"{row['career']}: {row['description']}"
    return "Career not found."
