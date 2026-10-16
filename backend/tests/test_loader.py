import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.opendota_client import OpenDotaClient


def test_normalize_hero_ok():
    h = OpenDotaClient.normalize_hero({"id": 1, "name": "npc_dota_hero_antimage",
                                       "localized_name": "Anti-Mage", "roles": ["Carry"]})
    assert h and h["id"] == 1 and "Carry" in h["roles"]


def test_normalize_hero_bad():
    assert OpenDotaClient.normalize_hero({"id": -1}) is None
    assert OpenDotaClient.normalize_hero({}) is None


def test_normalize_matchup_ok():
    m = OpenDotaClient.normalize_matchup(1, {"hero_id": 2, "wins": 53, "games_played": 100})
    assert m and m["win_rate"] == 0.53 and m["patch"] == "unknown"


def test_normalize_matchup_rejects_bad():
    assert OpenDotaClient.normalize_matchup(1, {"hero_id": 1, "wins": 1, "games_played": 2}) is None
    assert OpenDotaClient.normalize_matchup(1, {"hero_id": 2, "wins": 5, "games_played": 3}) is None
    assert OpenDotaClient.normalize_matchup(1, {}) is None
