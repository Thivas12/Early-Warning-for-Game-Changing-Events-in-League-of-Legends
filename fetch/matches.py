import re
import time
import pandas as pd
from .ladder import riot_session, REGION_MAP


def get_region_for_match_id(match_id_str):
    """
    It gets the game region from a match ID, or use "europe" if its unknown.
    """
    platform_id = match_id_str.split("_", 1)[0]
    return REGION_MAP.get(platform_id, "europe")


def normalize_match_id(match_id_raw_string):
    """
    It cleans a match ID by removing spaces and keeping the format "PLATFORMID_XXXXXXXXXX", or return None if its invalid.
    """
    cleaned = re.sub(r"\s+", "", str(match_id_raw_string).strip())
    match = re.search(r"([A-Za-z0-9]+_\d+)", cleaned)
    return match.group(1).upper() if match else None

def riot_get_match_or_timeline(url, params=None):
    """
    It gets match or timeline data from Riot API and retries if the rate limit is hit.
    """
    resp = riot_session.get(url, params=params, timeout=25)
    if resp.status_code == 429:
        wait_time = int(resp.headers.get("Retry-After", "2"))
        time.sleep(wait_time)
        return riot_get_match_or_timeline(url, params)
    if resp.status_code >= 400:
        print(resp.text)
        resp.raise_for_status()

    return resp.json()


def fetch_match_obj(match_id):
    """
    It will retrieve the full match object for a given match ID.
    """
    region = get_region_for_match_id(match_id)
    url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    return riot_get_match_or_timeline(url)


def fetch_timeline_obj(match_id):
    """
    It will retrieve the full timeline object for a given match ID.
    """
    region = get_region_for_match_id(match_id)
    url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
    return riot_get_match_or_timeline(url)


def get_clean_match_id_list_from_csv(path_to_csv):
    """
    It loads a CSV and get a clean, unique list of match IDs from columns named "matchid", "match_id", "gameid", or "game_id". Raise an error if no such column is found.
    (Scraped from Kaggle just to mirror some match IDs, since its extremely complex to do timlelines properly otherwise)
    """
    df = pd.read_csv(path_to_csv)
    match_col = next(
        (col for col in df.columns if col.lower() in {"matchid", "match_id", "gameid", "game_id"}),
        None
    )

    if match_col is None:
        raise ValueError("No valid match ID column found in CSV!")

    raw_ids = df[match_col].astype(str).tolist()
    normalized_ids = [normalize_match_id(rawid) for rawid in raw_ids]
    return [x for x in pd.unique(pd.Series(normalized_ids)) if x]
