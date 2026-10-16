"""Тесты Agent 6 (6.9): основные сценарии интерфейса + контракт с backend.
Без Node: статические проверки HTML/JS + API-контракт через TestClient."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def test_html_has_draft_controls():
    html = _read("frontend/index.html")
    for el in ["radiantPicks", "direPicks", "radiantBans", "direBans", "teamToPick",
               "roleFilter", "limit", "recommendBtn", "retryBtn", "clearBtn",
               "search", "pickTarget", "heroGrid", "recList", "status", "loading",
               "warnStale", "warnLow", "backendUrl"]:
        assert f'id="{el}"' in html, f"missing #{el}"


def test_html_has_menu_tabs():
    """Новое меню: одна точка входа, 4 раздела (драфт/топ/новости/настройки)."""
    html = _read("frontend/index.html")
    for tab in ["tab-draft", "tab-top", "tab-news", "tab-settings"]:
        assert f'id="{tab}"' in html, f"missing {tab}"
    assert "overlay.html" in html
    for el in ["topList", "newsList", "defLimit", "overlayOpacity", "saveSettings"]:
        assert f'id="{el}"' in html, f"missing #{el}"


def test_overlay_window():
    """Окно 1: оверлей — боковые меню + кнопка меню + центр контрпиков."""
    html = _read("frontend/overlay.html")
    for el in ["ovSearchR", "ovSearchD", "ovListR", "ovListD", "ovGridR", "ovGridD",
               "ovRecs", "ovRadiant", "ovDire"]:
        assert f'id="{el}' in html, f"missing #{el}"
    assert "index.html" in html  # одна кнопка в меню
    js = _read("frontend/overlay.js")
    assert "/recommendations" in js and "/heroes" in js
    assert "smoothed" not in js.lower() and "w_c" not in js  # счёт только в backend


def test_html_accessibility_basics():
    html = _read("frontend/index.html")
    assert 'lang="ru"' in html
    assert "<label" in html and "aria-live" in html
    assert "skip" in html  # skip-link


def test_js_no_local_scoring():
    """6.5: рекомендации из backend, UI не считает score (эвристика)."""
    js = _read("frontend/app.js")
    assert "/recommendations" in js and "/explain" in js
    assert "w_c" not in js and "smoothed" not in js.lower()
    # запрет дубля и лимит слотов
    assert "selectedAll().has" in js and "MAX_PICKS" in js


def test_js_handles_states():
    js = _read("frontend/app.js")
    for s in ["loading", "retryBtn", "Пусто", "Ошибка API", "warnStale", "warnLow", "Ничего не найдено"]:
        assert s in js, f"missing state: {s}"


def test_api_contract_for_frontend():
    from app.main import app
    c = TestClient(app)
    heroes = c.get("/heroes").json()
    assert len(heroes["heroes"]) >= 10
    req = {"radiant_picks": [1], "dire_picks": [8], "radiant_bans": [], "dire_bans": [],
           "team_to_pick": "radiant", "requested_roles": [], "limit": 5}
    rec = c.post("/recommendations", json=req).json()
    r0 = rec["recommendations"][0]
    assert {"hero_id", "score", "confidence", "reasons", "caveats"} <= set(r0)
    assert all("games_played" in x for x in r0["reasons"])
    assert 1 not in {x["hero_id"] for x in rec["recommendations"]}  # picked исключён
