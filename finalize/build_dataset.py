import os
import pandas as pd
from .labels import create_target_variables

def load_data_for_finalizing(csv_path):
    """
    It loads the CSV file and makes sure it actually exists.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError("File missing: " + csv_path)
    data = pd.read_csv(csv_path)
    print(f"Loaded data with {len(data)} rows")
    return data

def prepare_cleaned_data(df):
    """
    It cleans the data by removing bad rows and filling in missing values.
    """
    df_cleaned = df.copy()
    df_cleaned.dropna(subset=["gold_14", "xp_14", "gold_20", "xp_20"], inplace=True)
    df_cleaned["damage_20"].fillna(df_cleaned["damage_20"].median(), inplace=True)
    for col in ["gold_14", "xp_14", "gold_20", "xp_20", "damage_20"]:
        df_cleaned = df_cleaned[df_cleaned[col] >= 0]
    df_cleaned.drop_duplicates(inplace=True)
    print(f"Cleaned data rows: {len(df_cleaned)}")
    return df_cleaned

def save_by_role_datasets(df, output_folder):
    """
    It saves the dataset as both a full version and split by player roles.
    """
    os.makedirs(output_folder, exist_ok=True)
    full_path = os.path.join(output_folder, "full_dataset.csv")
    df.to_csv(full_path, index=False)
    print(f"Saved full dataset to {full_path}")
    role_folder = os.path.join(output_folder, "by_role")
    os.makedirs(role_folder, exist_ok=True)
    for r in df["role"].unique():
        subset = df[df["role"] == r]
        path = os.path.join(role_folder, f"{r.lower()}_dataset.csv")
        subset.to_csv(path, index=False)
        print(f"Saved {r} dataset with {len(subset)} rows")

def build_final_dataset(input_csv, output_dir="./data/processed"):
    """
    It takes raw data and turns it into a clean, final dataset ready for analysis.
    """
    print("Loading and cleaning data...")
    df = load_data_for_finalizing(input_csv)
    df = prepare_cleaned_data(df)
    print("Adding targets...")
    df = create_target_variables(df)
    print("Saving datasets...")
    save_by_role_datasets(df, output_dir)
    print("Done!")
