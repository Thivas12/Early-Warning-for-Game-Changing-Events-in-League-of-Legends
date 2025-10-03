import json, pandas as pd
from pathlib import Path
from tqdm import tqdm

RAW_TL_DIR = Path("data/raw/timelines")
OUT = Path("data/processed/events.csv")

def flatten_events(mid, tl):
    """
    Extract and format timeline events to faltten for a match.
    """
    out=[]
    for fr in tl.get("info",{}).get("frames",[]):
        fts=int((fr.get("timestamp") or 0)//1000)
        for ev in fr.get("events",[]):
            t=int((ev.get("timestamp") or fts)//1000)
            out.append({"match_id":mid,"t":t,**{k:ev.get(k) for k in["type","teamId","killerId","victimId","killerTeamId","monsterType","monsterSubType","buildingType","towerType","laneType","itemId"]}})
    return out

def process_events():
    """
    Flatten all timeline JSONs into a single events CSV.
    """
    rows=[]
    for p in tqdm(RAW_TL_DIR.glob("*.json"), desc="Flatten events"):
        tl=json.loads(p.read_text()); mid=tl.get("metadata",{}).get("matchId")
        if mid: rows+=flatten_events(mid,tl)
    df=pd.DataFrame(rows).sort_values(["match_id","t"]).reset_index(drop=True)
    df.to_csv(OUT,index=False); return df
