from flatten.timeline import pick_closest_frame, get_damage_for_participant_at_frame
from .events import kda_until, team_objectives_until


ROLE_MAP = {"TOP": "TOP", "JUNGLE": "JUNGLE", "MIDDLE": "MID", "BOTTOM": "ADC", "UTILITY": "SUPPORT"}


def rows_from_match_and_timeline(match, timeline):
    """
    It takes match and timeline data and turns it into rows for the dataset.
    """
    info = match["info"]
    frames = timeline["info"]["frames"]
    players = info["participants"]

    f14 = pick_closest_frame(frames, 14 * 60 * 1000)
    f20 = pick_closest_frame(frames, 20 * 60 * 1000)
    if f14 is None or f20 is None:
        return []

    team_objectives_by_14 = team_objectives_until(frames, 14 * 60 * 1000)
    result_rows = []

    for participant in players:
        pid = participant["participantId"]
        teamId = participant["teamId"]
        role_raw = (participant.get("teamPosition") or "").upper()
        if role_raw not in ROLE_MAP:
            continue
        role = ROLE_MAP[role_raw]

        stats_14 = f14["participantFrames"].get(str(pid), {})
        gold_14 = stats_14.get("totalGold")
        xp_14 = stats_14.get("xp")
        kills, deaths, assists = kda_until(frames, 14 * 60 * 1000, pid)

        stats_20 = f20["participantFrames"].get(str(pid), {})
        gold_20 = stats_20.get("totalGold")
        xp_20 = stats_20.get("xp")
        damage_20 = get_damage_for_participant_at_frame(f20, pid)
        if damage_20 is None:
            damage_20 = 0
        elif damage_20 > 10000:
            damage_20 = damage_20 / 100.0

        team_obj = team_objectives_by_14[teamId]

        row = {
            "matchId": match["metadata"]["matchId"],
            "queueId": info.get("queueId"),
            "gameVersion": info.get("gameVersion"),
            "teamId": teamId,
            "role": role,
            "champion": participant.get("championName"),
            "gold_14": gold_14,
            "xp_14": xp_14,
            "kills_14": kills,
            "deaths_14": deaths,
            "assists_14": assists,
            "plates_14": team_obj["plates"],
            "towers_14": team_obj["towers"],
            "dragons_14": team_obj["dragon"],
            "heralds_14": team_obj["herald"],
            "grubs_14": team_obj["grubs"],
            "gold_20": gold_20,
            "xp_20": xp_20,
            "damage_20": damage_20,
        }
        result_rows.append(row)

    return result_rows
