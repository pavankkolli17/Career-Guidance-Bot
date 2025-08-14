import pandas as pd

def get_all_careers():
    df = pd.read_csv('data/careers.csv')
    return df['career'].tolist()

def get_career_details(career_name):
    df = pd.read_csv('data/careers.csv')
    for _, row in df.iterrows():
        if row['career'].strip().lower() == career_name.strip().lower():
            return f"{row['career']}: {row['description']}"
    return "Career not found."