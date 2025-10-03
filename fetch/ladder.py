import os, time
from dotenv import load_dotenv
from tqdm import tqdm
from riotwatcher import LolWatcher, ApiError

load_dotenv()
API_KEY = (os.getenv("RIOT_API_KEY") or "").strip().replace("\u200b", "")


PLATFORM = "euw1"   
REGION   = "europe" 
QUEUE    = "RANKED_SOLO_5x5"

watcher = LolWatcher(API_KEY)


def get_ladder_entries():
    """
    Fetch top-ranked players from Challenger, falling back to Grandmaster or Master if needed.
    """
    for tier_func, args in [
    (watcher.league.challenger_by_queue, (PLATFORM, QUEUE)),
    (watcher.league.grandmaster_by_queue, (PLATFORM, QUEUE)),
    (watcher.league.masters_by_queue, (PLATFORM, QUEUE)),  
    ]:

        try:
            lad = tier_func(*args)
            ents = lad.get("entries", [])
            if ents:
                print(f"Found {len(ents)} entries in {tier_func.__name__}")
                return ents
        except Exception as e:
            print(f"Failed {tier_func.__name__}: {e}")
            continue
    return []


def resolve_puuid(entry):
    """
    Convert a ladder entry into a PUUID using summonerId or summonerName.
    """
    try:
        if entry.get("summonerId"):
            return watcher.summoner.by_id(PLATFORM, entry["summonerId"])["puuid"]
        if entry.get("summonerName"):
            return watcher.summoner.by_name(PLATFORM, entry["summonerName"])["puuid"]
        if entry.get("puuid"):
            return entry["puuid"]
    except ApiError as e:
        code = getattr(e.response, "status_code", None)
        print(f"ApiError resolving PUUID: {code} for {entry.get('summonerName','?')}")
    return None


def fetch_seed_puuids(limit=200):
    """
    Collect seed PUUIDs from ladder entries, deduplicated.
    """
    entries = get_ladder_entries()
    if not entries:
        print("No ladder entries fetched. Check API key or region.")
        return []

    seed_puuids = []
    for e in tqdm(entries[:limit], desc="Fetch PUUIDs"):
        puuid = resolve_puuid(e)
        if puuid:
            seed_puuids.append(puuid) 
        else:
            time.sleep(0.1) 

    seed_puuids = list(dict.fromkeys(seed_puuids))  
    print(f"Collected {len(seed_puuids)} PUUIDs")
    return seed_puuids
