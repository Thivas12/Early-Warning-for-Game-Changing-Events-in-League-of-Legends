def kda_until(frames, cutoff_ms, pid):
    """
    It counts kills, deaths, and assists for a player up to a certain time.
    """
    kills = deaths = assists = 0
    for frame in frames:
        if frame["timestamp"] > cutoff_ms:
            break
        for event in frame.get("events", []):
            if event.get("type") == "CHAMPION_KILL":
                if event.get("killerId") == pid:
                    kills += 1
                if event.get("victimId") == pid:
                    deaths += 1
                if pid in (event.get("assistingParticipantIds") or []):
                    assists += 1
    return kills, deaths, assists

def team_objectives_until(frames, cutoff_ms):
    """
    It tallies up dragons, barons, towers and other objectives taken by each team.
    """
    tally = {
        100: {"dragon":0, "herald":0, "baron":0, "plates":0, "towers":0, "grubs":0},
        200: {"dragon":0, "herald":0, "baron":0, "plates":0, "towers":0, "grubs":0}
    }
    for frame in frames:
        if frame["timestamp"] > cutoff_ms:
            break
        for event in frame.get("events", []):
            etype = event.get("type")
            if etype == "ELITE_MONSTER_KILL":
                team = event.get("killerTeamId")
                mtype = (event.get("monsterType") or "").upper()
                msub = (event.get("monsterSubType") or "").upper()
                if team in (100, 200):
                    if mtype == "DRAGON":
                        tally[team]["dragon"] += 1
                    elif mtype == "BARON_NASHOR":
                        tally[team]["baron"] += 1
                    elif mtype == "RIFTHERALD":
                        tally[team]["herald"] += 1
                    if any(x in msub for x in ["VOID", "GRUB", "HORDE"]):
                        tally[team]["grubs"] += 1
            elif etype == "BUILDING_KILL":
                lost_team = event.get("teamId")
                got_team = 100 if lost_team == 200 else 200 if lost_team == 100 else None
                if event.get("buildingType") == "TOWER_BUILDING" and got_team:
                    tally[got_team]["towers"] += 1
            elif etype == "TURRET_PLATE_DESTROYED":
                lost_team = event.get("teamId")
                got_team = 100 if lost_team == 200 else 200 if lost_team == 100 else None
                if got_team:
                    tally[got_team]["plates"] += 1
    return tally
