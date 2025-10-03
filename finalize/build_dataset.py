import pandas as pd
from pathlib import Path

def build_final(matches_df, timeline_df, labels_df):
    """
    Build and save the final wide-format dataset for analysis.
    """
    for c in [f"{side}{i}" for side in("blue","red") for i in range(5)]:
        if c in matches_df: 
            matches_df[c]=pd.to_numeric(matches_df[c],errors="coerce").fillna(0).astype("int64").clip(0,300)
    wide=timeline_df.merge(matches_df,on="match_id",how="left")
    if not labels_df.empty: wide=wide.merge(labels_df,on=["match_id","t"],how="left")
    out=Path("data/processed/lol_ranked_2024_2025_timeseries_10s.csv")
    wide.to_csv(out,index=False); return out,wide.shape
