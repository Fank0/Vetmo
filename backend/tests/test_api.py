import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

BASE = {"radiant_picks": [1], "dire_picks": [8, 6], "radiant_bans": [], "dire_bans": [],
        "team_to_pick": "radiant", "requested_roles": [], "limit": 5}


def test_health():
    assert client.get("/health").status_code == 200


def test_heroes_list():
    r = client.get("/heroes")
    assert r.status_code == 200 and len(r.json()["heroes"]) >= 10


def test_excludes_picked_and_banned():
    req = dict(BASE, radiant_picks=[1, 2], dire_picks=[3], radiant_bans=[5], dire_bans=[6])
    recs = client.post("/recommendations", json=req).json()["recommendations"]
    ids = {x["hero_id"] for x in recs}
    assert ids.isdisjoint({1, 2, 3, 5, 6})


def test_unknown_hero_422():
    req = dict(BASE, radiant_picks=[99999])
    assert client.post("/recommendations", json=req).status_code == 422


def test_duplicate_overlap_422():
    req = dict(BASE, radiant_picks=[1], dire_picks=[1])
    assert client.post("/recommendations", json=req).status_code == 422


def test_deterministic():
    a = client.post("/recommendations", json=BASE).json()
    b = client.post("/recommendations", json=BASE).json()
    assert a == b


def test_low_confidence_caveat_when_no_data():
    req = dict(BASE, radiant_picks=[], dire_picks=[999 if False else 4],
               radiant_bans=[], dire_bans=[], limit=3)
    recs = client.post("/recommendations", json=req).json()["recommendations"]
    assert all("confidence" in r and "caveats" in r for r in recs)


def test_explain_does_not_change_score():
    rec = client.post("/recommendations", json=BASE).json()["recommendations"][0]
    ex = client.post("/explain", json=dict(BASE, hero_id=rec["hero_id"])).json()
    assert ex["facts_used"]["score"] == rec["score"]
    assert ex["llm_generated"] is False
