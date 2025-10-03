from fetch.ladder import fetch_seed_puuids
from fetch.matches import fetch_match_ids
from fetch.download import download_all
from flatten.matches import flatten_matches
from flatten.events import process_events
from flatten.timeline import build_timelines
from finalize.labels import make_labels
from finalize.build_dataset import build_final

def main():
    """
    Run the full League of Legends data pipeline step by step.
    """
    print("\n=== STEP 1: Fetch seed players ===")
    puuids = fetch_seed_puuids(limit=200)
    print(f"Collected {len(puuids)} PUUIDs")

    print("\n=== STEP 2: Fetch match IDs ===")
    mids_df = fetch_match_ids(puuids, pages=1, per_page=100)
    print(f"Fetched {len(mids_df)} match IDs ({mids_df['match_id'].nunique()} unique)")

    print("\n=== STEP 3: Download raw matches & timelines ===")
    download_all(mids_df["match_id"].unique())

    print("\n=== STEP 4: Flatten matches ===")
    matches_df = flatten_matches()
    print(f"Matches flattened: {matches_df.shape}")

    print("\n=== STEP 5: Flatten events ===")
    events_df = process_events()
    print(f"Events flattened: {events_df.shape}")

    print("\n=== STEP 6: Build per-10s timelines ===")
    timeline_df = build_timelines(events_df)
    print(f"Timelines built: {timeline_df.shape}")

    print("\n=== STEP 7: Generate labels ===")
    labels_df = make_labels(events_df, timeline_df, horizons=(10,20,30))
    print(f"Labels generated: {labels_df.shape}")

    print("\n=== STEP 8: Finalize dataset ===")
    out, shape = build_final(matches_df, timeline_df, labels_df)
    print(f"Final dataset saved: {out} ({shape})")

if __name__ == "__main__":
    main()
