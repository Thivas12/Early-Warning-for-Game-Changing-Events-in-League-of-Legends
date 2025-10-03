import json
from pathlib import Path
from tqdm import tqdm
from riotwatcher import ApiError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .ladder import watcher, REGION

RAW_MATCH_DIR = Path("data/raw/matches"); RAW_MATCH_DIR.mkdir(parents=True, exist_ok=True)
RAW_TL_DIR    = Path("data/raw/timelines"); RAW_TL_DIR.mkdir(parents=True, exist_ok=True)

@retry(retry=retry_if_exception_type(ApiError), wait=wait_exponential(min=1,max=60), stop=stop_after_attempt(5), reraise=True)
def fetch_match(mid):
    """
    Fetch match data from Riot API by match ID.
    """
    return watcher.match.by_id(REGION, mid)

@retry(retry=retry_if_exception_type(ApiError), wait=wait_exponential(min=1,max=60), stop=stop_after_attempt(5), reraise=True)
def fetch_timeline(mid):
    """
    Fetch timeline data from Riot API by match ID.
    """
    return watcher.match.timeline_by_match(REGION, mid)

def download_all(match_ids):
    """
    Download all matches and timelines and saving them as JSON files.
    """
    ok_m=ok_tl=miss_tl=0
    for mid in tqdm(match_ids, desc="Download match & timeline"):
        m_path, tl_path = RAW_MATCH_DIR/f"{mid}.json", RAW_TL_DIR/f"{mid}.json"
        if not m_path.exists():
            try: m_path.write_text(json.dumps(fetch_match(mid))); ok_m+=1
            except ApiError: pass
        if not tl_path.exists():
            try: tl_path.write_text(json.dumps(fetch_timeline(mid))); ok_tl+=1
            except ApiError: miss_tl+=1
    print(f"matches:{ok_m}, timelines:{ok_tl}, missing:{miss_tl}")
