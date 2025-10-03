import time, pandas as pd
from tqdm import tqdm
from riotwatcher import ApiError
from datetime import datetime, timezone
from pathlib import Path
from .ladder import watcher, REGION, fetch_seed_puuids

DATA_DIR = Path("data/interim"); DATA_DIR.mkdir(parents=True, exist_ok=True)
QUEUE_ID = 420
START = int(datetime(2024,1,1,tzinfo=timezone.utc).timestamp())
END   = int(datetime(2025,12,31,23,59,59,tzinfo=timezone.utc).timestamp())

def match_ids_by_puuid(puuid, start=0, count=100):
    """
    Get match IDs for a player using their PUUID.
    """
    try:
        return watcher.match.matchlist_by_puuid(REGION, puuid, start=start, count=count,
            queue=QUEUE_ID, start_time=START, end_time=END)
    except TypeError:  
        return watcher.match.matchlist_by_puuid(REGION, puuid, start=start, count=count,
            queue=QUEUE_ID, startTime=START, endTime=END)

def fetch_match_ids(puuids, pages=1, per_page=100):
    """
    Fetch and save match IDs for a list of PUUIDs.
    """
    recs = []
    for puuid in tqdm(puuids, desc="Match IDs by PUUID"):
        for p in range(pages):
            try:
                mids = match_ids_by_puuid(puuid, start=p*per_page, count=per_page)
                if not mids: break
                recs += [{"puuid": puuid, "match_id": mid} for mid in mids]
            except ApiError as e:
                if getattr(e.response,"status_code",None)==429: time.sleep(2)
                break
    df = pd.DataFrame(recs).drop_duplicates()
    df.to_csv(DATA_DIR/"match_ids.csv", index=False)
    return df
