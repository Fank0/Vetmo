import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.scoring import smoothed_winrate, confidence_for, score_candidate, HeroRow, MatchupRow


def test_smoothing():
    assert smoothed_winrate(0, 0) == 0.5
    assert 0.5 < smoothed_winrate(53, 100) < 0.53  # стягивание к приору
    assert smoothed_winrate(900, 1000) > 0.85


def test_confidence_thresholds():
    assert confidence_for(10) == "low"
    assert confidence_for(150) == "medium"
    assert confidence_for(500) == "high"


def test_role_fit():
    h = HeroRow(id=5, localized_name="CM", roles=["Support"])
    mm = {}
    s1, _, r1, _, _ = score_candidate(h, [], mm, None, ["Support"])
    s2, _, r2, _, _ = score_candidate(h, [], mm, None, ["Carry"])
    assert s1 > s2
    assert any(x["type"] == "role" for x in r1)


def test_counter_prefers_good_matchup():
    good = HeroRow(id=7, localized_name="ES", roles=["Support"])
    bad = HeroRow(id=5, localized_name="CM", roles=["Support"])
    mm_good = {8: MatchupRow(7, 8, 300, 200)}
    mm_bad = {8: MatchupRow(5, 8, 300, 80)}
    s_good, c_good, _, _, _ = score_candidate(good, [8], mm_good, None, [])
    s_bad, _, _, _, _ = score_candidate(bad, [8], mm_bad, None, [])
    assert s_good > s_bad and c_good in ("medium", "high")
