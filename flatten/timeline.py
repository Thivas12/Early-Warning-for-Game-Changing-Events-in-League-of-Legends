import json, pandas as pd
from pathlib import Path
from tqdm import tqdm

RAW_TL_DIR=Path("data/raw/timelines")
RAW_MATCH_DIR=Path("data/raw/matches")
OUT=Path("data/processed/timeline_10s.csv")

def timeline_10s(mid, tl, ev_df, tick=10):
    """
    Build a per 10s timeline of match stats and events.
    """
    m=json.loads((RAW_MATCH_DIR/f"{mid}.json").read_text())
    dur=int(m["info"].get("gameDuration",0)) or int((tl["info"]["frames"][-1]["timestamp"] or 0)//1000)
    if dur<=0: return None
    ts=range(0,(dur//tick)*tick+1,tick)
    df=pd.DataFrame({"match_id":mid,"t":ts,
                     "kills_blue":0,"kills_red":0,"dragons_blue":0,"dragons_red":0,
                     "heralds_blue":0,"heralds_red":0,"barons_blue":0,"barons_red":0,
                     "towers_blue":0,"towers_red":0})
    
    def team(pid): 
        return 100 if pid and int(pid)<=5 else 200
    for _,e in ev_df[ev_df["match_id"]==mid].iterrows():
        t=e.t//tick*tick; typ=e.type; teamId=e.teamId or e.killerTeamId
        if typ=="CHAMPION_KILL": teamId=teamId or team(e.killerId)
        if typ=="CHAMPION_KILL": df.loc[df.t>=t, f"kills_{'blue' if teamId==100 else 'red'}"]+=1
        elif typ=="ELITE_MONSTER_KILL":
            mon=e.monsterType; side="blue" if teamId==100 else "red"
            if mon=="DRAGON": df.loc[df.t>=t,f"dragons_{side}"]+=1
            elif mon=="RIFTHERALD": df.loc[df.t>=t,f"heralds_{side}"]+=1
            elif mon=="BARON_NASHOR": df.loc[df.t>=t,f"barons_{side}"]+=1
        elif typ=="BUILDING_KILL" and e.buildingType=="TOWER_BUILDING":
            side="blue" if teamId==100 else "red"; df.loc[df.t>=t,f"towers_{side}"]+=1
            
    pm=[{"t":int(fr["timestamp"]//1000),
         "gold_blue":sum(v["totalGold"] for k,v in fr["participantFrames"].items() if int(k)<=5),
         "gold_red": sum(v["totalGold"] for k,v in fr["participantFrames"].items() if int(k)>5),
         "xp_blue":  sum(v["xp"] for k,v in fr["participantFrames"].items() if int(k)<=5),
         "xp_red":   sum(v["xp"] for k,v in fr["participantFrames"].items() if int(k)>5)}
        for fr in tl["info"]["frames"] if fr.get("participantFrames")]
    if pm:
        pm=pd.DataFrame(pm).sort_values("t")
        merged=pd.merge_asof(pd.DataFrame({"t":ts}),pm,on="t",direction="backward").fillna(0)
        df=df.merge(merged,on="t",how="left")
    df["gold_diff"]=df.gold_blue-df.gold_red
    df["xp_diff"]=df.xp_blue-df.xp_red
    return df

def build_timelines(ev_df):
    """
    Generate per 10s timelines for all matches and save as CSV.
    """
    parts=[]
    for p in tqdm(RAW_TL_DIR.glob("*.json"), desc="Per-10s timelines"):
        tl=json.loads(p.read_text()); mid=tl["metadata"]["matchId"]
        part=timeline_10s(mid,tl,ev_df); 
        if part is not None: parts.append(part)
    df=pd.concat(parts,ignore_index=True) if parts else pd.DataFrame()
    df.to_csv(OUT,index=False); return df
