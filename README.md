# Early Warning for Game-Changing Events in League of Legends

This repository contains the full data collection and processing pipeline used to build the **LOL Dataset**, a structured dataset of Challenger-tier ranked matches from the EUW server. The data is collected directly from the **Riot Games API**, transformed into player, team, and timeline-level views, and prepared for analytics and machine learning tasks such as predicting major in-game events (Baron, Dragon, teamfights, etc.).

---

## Dataset on Kaggle

The complete dataset is publicly available on Kaggle:  
[LOL Dataset on Kaggle](https://www.kaggle.com/datasets/keerthivasankannan/lol-dataset)

---

## Repository Structure
- **`fetch/`** 
  - `ladder.py` 
  - `matches.py`  
  - `download.py` 

- **`flatten/`** 
  - `matches.py` 
  - `events.py` 
  - `timeline.py` 

- **`finalize/`** 
  - `labels.py`  
  - `build_dataset.py` 

- **`data/`** 
  - `raw/` 
  - `interim/` 
  - `processed/` 

- **`main.py`** 
- **`requirements.txt`** 
- **`.gitignore`** 


---

## How It Works

1. **Fetch Ladder Data**  
   - Collects Challenger (or fallback Grandmaster/Master) player PUUIDs using the Riot API.  
   - Stored locally for match lookup.

2. **Collect Match Data**  
   - Retrieves match IDs for each player (Ranked Solo, EUW region).  
   - Downloads detailed match and timeline JSONs.

3. **Flatten Data**  
   - Extracts per-player and per-team statistics.  
   - Processes event timelines into structured CSV files.

4. **Build Features & Labels**  
   - Aggregates timeline metrics (gold, XP, kills) in 10-second intervals.  
   - Labels key in-game events (e.g., Baron, Dragon, teamfights).

5. **Assemble Final Dataset**  
   - Combines player stats, timeline features, and event labels.  
   - Produces a clean, analysis-ready dataset.

---

## Dataset Overview

| File | Description |
|------|--------------|
| `player_stats.csv` | Player-level statistics (kills, deaths, assists, damage, wards, healing, etc.) |
| `events.csv` | Flattened timeline events (kills, dragons, barons, turrets, etc.) |
| `timeline_10s.csv` | Team-level economy and XP stats at 10-second intervals |
| `labels.csv` | Binary indicators for future objectives or fights |
| `final_dataset.csv` | Combined, ML-ready dataset with features and labels |

---

## Requirements
- riotwatcher==3.3.0
- pandas>=2.0.0
- numpy>=1.24.0
- python-dotenv>=1.0.0
- tqdm>=4.66.0
- tenacity>=8.2.0




