import numpy as np, pandas as pd
OUT="data/processed/labels.csv"

def make_labels(events_df, timeline_10s_df, horizons=(10,20,30)):
    """
    Create future event labels for each match and time horizon.
    """
    out=[]
    for mid,g in events_df.groupby("match_id"):
        g=g.sort_values("t"); T=int(g.t.max() or 0)
        if T==0: continue
        baron,dragon,tfkill=np.zeros(T+1,bool),np.zeros(T+1,bool),np.zeros(T+1,bool)
        for _,e in g.iterrows():
            t=int(e.t)
            if e.type=="ELITE_MONSTER_KILL" and e.monsterType=="BARON_NASHOR": baron[t]=True
            if e.type=="ELITE_MONSTER_KILL" and e.monsterType=="DRAGON": dragon[t]=True
            if e.type=="CHAMPION_KILL": tfkill[t]=True
        base=timeline_10s_df[timeline_10s_df.match_id==mid].copy()
        for h in horizons:
            def ahead(arr,t,h): return int(arr[min(t+1,T):min(t+h,T)+1].any())
            for name,arr in [("baron",baron),("dragon",dragon),("teamfight",tfkill)]:
                base[f"y_{name}_{h}"]=[ahead(arr,t,h) for t in base.t]
        out.append(base[["match_id","t"]+[f"y_{n}_{h}" for n in["baron","dragon","teamfight"] for h in horizons]])
    df=pd.concat(out,ignore_index=True) if out else pd.DataFrame()
    df.to_csv(OUT,index=False); return df
