import json, re, pandas as pd
from pathlib import Path
from tqdm import tqdm

RAW_MATCH_DIR = Path("data/raw/matches")
OUT = Path("data/processed/matches.csv")

def short_patch(ver):
    """
    Extract the major and minor version from a patch string.
    """
    m=re.match(r"(\d+)\.(\d+)", ver or "")
    return f"{m[1]}.{m[2]}" if m else ""

def flatten_matches():
    """
    Flatten raw match JSON files into a CSV table.
    """
    rows=[]
    for p in tqdm(RAW_MATCH_DIR.glob("*.json"), desc="Flatten matches"):
        m=json.loads(p.read_text()); info=m.get("info",{}); parts=info.get("participants",[])
        blue,red = sorted([r["championId"] for r in parts if r["teamId"]==100]), sorted([r["championId"] for r in parts if r["teamId"]==200])
        if len(blue)!=5 or len(red)!=5: continue
        row={"match_id":m["metadata"]["matchId"],"patch":short_patch(info.get("gameVersion","")),
             "queueId":info.get("queueId"),"region":"europe","platform":"euw1",
             "game_start_utc":int(info.get("gameStartTimestamp") or info.get("gameCreation") or 0),
             "game_duration_s":int(info.get("gameDuration") or 0)}
        row.update({f"blue{i}":blue[i] for i in range(5)})
        row.update({f"red{i}": red[i]  for i in range(5)})
        rows.append(row)
    df=pd.DataFrame(rows).dropna(subset=["game_duration_s"])
    df.to_csv(OUT,index=False)
    return df
