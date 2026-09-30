"""Independent matching, temporal access, censoring, and measurement checks."""

from functools import lru_cache
from random import Random

import pytest

from research.compile_objective_onset import expand_match, summarize
from research.objective_onset import (
    Contact,
    Episode,
    audit_match,
    completion_window_overlap,
    contacts_from_gem,
    reactive_alarms,
    score_alarms,
    segment_episodes,
)


def test_matching_equals_exhaustive_assignment_and_counts_each_event_once():
    rng = Random(20260930)
    for _ in range(250):
        alarms = sorted(rng.randrange(20) for _ in range(rng.randrange(7)))
        targets = sorted(rng.randrange(25) for _ in range(rng.randrange(7)))
        low, high = rng.randrange(1, 5), rng.randrange(5, 11)

        @lru_cache(None)
        def brute(i, used, alarms=tuple(alarms), targets=tuple(targets), low=low, high=high):
            if i == len(alarms):
                return 0
            options = [brute(i + 1, used)]
            for j, event in enumerate(targets):
                if not used & (1 << j) and low <= event - alarms[i] <= high:
                    options.append(1 + brute(i + 1, used | (1 << j)))
            return max(options)

        report = score_alarms(alarms, targets, min_lead=low, max_lead=high)
        assert report["hits"] == brute(0, 0)
        assert report["hits"] + report["unmatched_alarms"] == len(alarms)
    assert score_alarms([0, 0, 0], [5], min_lead=5, max_lead=10)["hits"] == 1


def test_episode_closure_preserves_unsuccessful_and_censored_contacts():
    contacts = [Contact(0, "DAMAGE"), Contact(10, "DAMAGE"), Contact(25, "DAMAGE")]
    episodes, orphan = segment_episodes(contacts, quiet_ticks=10, recording_end=30)
    assert episodes == [
        Episode(0, 10, None, "quiet", 2),
        Episode(25, 25, None, "right_censored", 1),
    ]
    assert orphan == []
    # At exactly the quiet boundary, absence is still insufficient to close.
    assert segment_episodes(contacts, quiet_ticks=10, recording_end=35)[0][-1].closure == (
        "right_censored"
    )


def test_death_matches_only_observed_damage_and_resets_episode():
    contacts = [
        Contact(0, "DEATH"),
        Contact(3, "DAMAGE"),
        Contact(3, "DEATH"),
        Contact(7, "DAMAGE"),
        Contact(30, "DEATH"),
    ]
    episodes, orphan = segment_episodes(contacts, quiet_ticks=10, recording_end=40)
    assert episodes == [Episode(3, 3, 3, "death", 1), Episode(7, 7, None, "quiet", 1)]
    assert orphan == [0, 30]


def test_detector_ignores_future_deaths_and_is_prefix_consistent():
    contacts = [Contact(t, "DAMAGE") for t in (0, 1, 20, 21, 40)]
    kwargs = {"quiet_ticks": 10, "cooldown_ticks": 20, "delay_ticks": 2}
    full = reactive_alarms(contacts, **kwargs)
    assert full == [2, 22, 42]
    with_deaths = sorted(
        [*contacts, Contact(8, "DEATH"), Contact(22, "DEATH")], key=lambda x: x.tick
    )
    assert reactive_alarms(with_deaths, **kwargs) == full
    for cut in range(45):
        prefix = reactive_alarms([c for c in contacts if c.tick <= cut], **kwargs)
        assert [t for t in prefix if t <= cut] == [t for t in full if t <= cut]


def test_pure_detector_can_pass_completion_target_and_fail_onset_target():
    contacts = [
        Contact(t, kind)
        for t, kind in (
            (100, "DAMAGE"),
            (120, "DAMAGE"),
            (130, "DEATH"),
            (300, "DAMAGE"),
            (320, "DAMAGE"),
            (340, "DEATH"),
        )
    ]
    alarms = reactive_alarms(contacts, quiet_ticks=30, cooldown_ticks=60)
    assert score_alarms(alarms, [130, 340], min_lead=20, max_lead=60)["recall"] == 1
    assert score_alarms(alarms, [100, 300], min_lead=20, max_lead=60)["recall"] == 0
    episode = Episode(100, 120, 130, "death", 2)
    assert completion_window_overlap(episode, min_lead=20, max_lead=60) == 0.25


def test_source_adapter_does_not_invent_contact_from_a_modifier_or_zero_damage():
    rows = [
        {"tick": 1, "target_name": "roshan", "log_type": "MODIFIER_ADD", "value": 1},
        {"tick": 2, "target_name": "roshan", "log_type": "DAMAGE", "value": 0},
        {"tick": 3, "target_name": "other", "log_type": "DAMAGE", "value": 100},
        {"tick": 4, "target_name": "roshan", "log_type": "DAMAGE", "value": 1},
        {"tick": 5, "target_name": "roshan", "log_type": "DEATH"},
    ]
    assert contacts_from_gem({"combat_log": rows}, "roshan") == [
        Contact(4, "DAMAGE"),
        Contact(5, "DEATH"),
    ]
    with pytest.raises(ValueError, match="not ordered"):
        contacts_from_gem({"combat_log": list(reversed(rows))}, "roshan")


def test_terminal_coverage_disagreement_fails_instead_of_silent_exclusion():
    with pytest.raises(ValueError, match="independent objective list"):
        audit_match({"combat_log": [], "roshans": [{"tick": 10}]})


def test_empty_targets_and_invalid_windows():
    assert score_alarms([], [], min_lead=1, max_lead=2)["recall"] is None
    with pytest.raises(ValueError):
        score_alarms([0], [0], min_lead=0, max_lead=2)
    with pytest.raises(ValueError):
        segment_episodes([Contact(5, "DAMAGE")], quiet_ticks=2, recording_end=4)


def test_compact_facts_keep_reactive_reengagement_credit_visible():
    # Detecting one attack can incidentally precede a later episode. The onset
    # audit must report that credit rather than force a misleading zero result.
    match = {
        "match_id": 1,
        "start_tick": 0,
        "end_tick": 9000,
        "source_combat_records": 100,
        "contacts": [[3000, 0], [4200, 0], [4300, 1]],
    }
    payload = expand_match(match)
    assert [c.tick for c in contacts_from_gem(payload, "npc_dota_roshan")] == [3000, 4200, 4300]
    result = summarize(
        {"matches": [match], "source_revision": "test", "acquisition": {"attempted_matches": 1}}
    )
    primary = next(
        m
        for m in result["metrics"]
        if m["quiet_gap_seconds"] == 10
        and m["delivery_delay_seconds"] == 0
        and m["minimum_lead_seconds"] == 20
    )
    assert primary["onset_targets"] == 2
    assert primary["onset_hits"] == 1
    assert primary["alarms"] == 1
    assert result["independent_matches"] == 1
    assert result["source_combat_records"] == 100
