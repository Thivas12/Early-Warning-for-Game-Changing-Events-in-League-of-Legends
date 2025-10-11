import os
import time
import pandas as pd
from tqdm import tqdm
from .matches import fetch_match_obj, fetch_timeline_obj, get_clean_match_id_list_from_csv
from flatten.matches import rows_from_match_and_timeline

def download_and_save_matches(csv_path, save_file_path="./lol_14to20_from_api.csv"):
    """
    It downloads match data from the API and saves it to CSV, with resume capability.
    """
    match_id_list = get_clean_match_id_list_from_csv(csv_path)
    print(f"Total matches to process: {len(match_id_list)}")
    
    processed_matches = set()
    if os.path.exists(save_file_path):
        try:
            existing_df = pd.read_csv(save_file_path, usecols=["matchId"])
            processed_matches = set(existing_df["matchId"].unique())
            print(f"Resuming. Already processed {len(processed_matches)} matches.")
        except:
            print("Could not read existing file; starting fresh.")
    
    collected_rows = []
    rows_since_last_save = 0
    save_batch_size = 300

    for match_id in tqdm(match_id_list, desc="Fetch and process matches"):
        if match_id in processed_matches:
            continue

        try:
            match_json = fetch_match_obj(match_id)
            timeline_json = fetch_timeline_obj(match_id)
            rows = rows_from_match_and_timeline(match_json, timeline_json)
            if rows:
                collected_rows.extend(rows)
                rows_since_last_save += len(rows)
        except Exception as error:
            print(f"Skipping {match_id} due to error: {error}")
            time.sleep(0.2)

        if rows_since_last_save >= save_batch_size:
            save_mode = "a" if os.path.exists(save_file_path) else "w"
            header_flag = not os.path.exists(save_file_path)
            pd.DataFrame(collected_rows).to_csv(save_file_path, mode=save_mode, header=header_flag, index=False)
            print(f"Saved batch of {rows_since_last_save} rows.")
            collected_rows = []
            rows_since_last_save = 0

    if collected_rows:
        save_mode = "a" if os.path.exists(save_file_path) else "w"
        header_flag = not os.path.exists(save_file_path)
        pd.DataFrame(collected_rows).to_csv(save_file_path, mode=save_mode, header=header_flag, index=False)
        print(f"Saved final batch of {len(collected_rows)} rows.")

    print(f"Done fetching. Data saved to {save_file_path}.")
