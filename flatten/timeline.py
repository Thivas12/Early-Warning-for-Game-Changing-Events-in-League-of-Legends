def pick_closest_frame(frames, target_milliseconds):
    """
    It finds the game frame thats closest to a specific time without going over.
    """
    filtered_frames = [frame for frame in frames if frame["timestamp"] <= target_milliseconds]
    if not filtered_frames:
        return None
    return max(filtered_frames, key=lambda f: f["timestamp"])

def get_damage_for_participant_at_frame(frame, participant_id):
    """
    It gets how much damage a player has dealt to champions at a specific game frame.
    """
    participant_frame = frame["participantFrames"].get(str(participant_id), {})
    damage_stats = participant_frame.get("damageStats", {})
    damage = damage_stats.get("totalDamageDoneToChampions")
    if damage and damage > 10000:
        damage = damage / 100.0
    return damage
