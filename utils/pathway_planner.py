import pandas as pd

def get_pathway(query):
    df = pd.read_csv('data/pathways.csv')
    for _, row in df.iterrows():
        if row['career'].lower() in query:
            return f"Pathway for {row['career']}: {row['steps']}"
    return "Pathway not found."
