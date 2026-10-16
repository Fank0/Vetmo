"""Draft Scoring API. Владелец: Agent 3. Контракты: docs/api-contracts.md (freeze: Agent 1)."""
from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .models import DraftRequest, DraftResponse, ExplainRequest, ExplainResponse, Recommendation, Reason
from .db import Store
from .scoring import HeroRow, score_candidate
from .explain import build_explanation
from .rag import search_similar

app = FastAPI(title="Dota 2 Drafter — Scoring API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _store() -> Store:
    return Store(settings.DATABASE_URL)


@app.get("/health")
def health():
    s = _store()
    return {"status": "ok", "db_mode": s.mode, "rag_enabled": settings.ENABLE_RAG}


@app.get("/heroes")
def heroes():
    s = _store()
    hs = s.heroes()
    return {"heroes": [{"id": h.id, "localized_name": h.localized_name, "roles": h.roles} for h in hs],
            "data_updated_at": s.data_updated_at(), "db_mode": s.mode}


def _recommend(req: DraftRequest, s: Store) -> DraftResponse:
    try:
        req.validate_no_overlap()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    heroes = s.hero_map()
    for hid in req.all_selected():
        if hid not in heroes:
            raise HTTPException(status_code=422, detail=f"unknown_hero_id: {hid}")
    enemy_picks = req.dire_picks if req.team_to_pick == "radiant" else req.radiant_picks
    excluded = req.all_selected()
    scored: list[tuple[float, int, Recommendation]] = []
    for hid, h in heroes.items():
        if hid in excluded:
            continue
        mm = {opp: s.matchup(hid, opp) for opp in enemy_picks}
        score, conf, reasons, caveats, _tg = score_candidate(
            HeroRow(id=h.id, localized_name=h.localized_name, roles=h.roles),
            enemy_picks, mm, s.meta_wr(hid), req.requested_roles,
            settings.SCORE_W_COUNTER, settings.SCORE_W_SYNERGY,
            settings.SCORE_W_ROLE, settings.SCORE_W_META, settings.SMOOTHING_K)
        scored.append((score, hid, Recommendation(hero_id=hid, score=score, confidence=conf,  # type: ignore
                                                 reasons=[Reason(**r) for r in reasons], caveats=caveats)))
    scored.sort(key=lambda x: (-x[0], x[1]))
    recs = [r for _, _, r in scored[:req.limit]]
    rag_ctx: list[dict] = []
    if settings.ENABLE_RAG:
        rag_ctx = search_similar(settings.QDRANT_URL, "draft_scenarios",
                                 req.radiant_picks, req.dire_picks, req.team_to_pick)
    return DraftResponse(recommendations=recs, data_updated_at=s.data_updated_at(),
                         rag_context=rag_ctx,
                         meta={"total_candidates": len(scored), "excluded": len(excluded),
                               "engine": "statistical-mvp-v1", "db_mode": s.mode})


@app.post("/recommendations", response_model=DraftResponse)
def recommendations(req: DraftRequest):
    return _recommend(req, _store())


@app.post("/explain", response_model=ExplainResponse)
def explain(req: ExplainRequest):
    base = DraftRequest(**req.model_dump(exclude={"hero_id"}))
    resp = _recommend(base, _store())
    rec = next((r for r in resp.recommendations if r.hero_id == req.hero_id), None)
    s = _store()
    hm = s.hero_map()
    if rec is None:
        if req.hero_id not in hm:
            raise HTTPException(status_code=422, detail=f"unknown_hero_id: {req.hero_id}")
        raise HTTPException(status_code=422, detail="hero not in candidate list (picked/banned or filtered)")
    enemy = (req.dire_picks if req.team_to_pick == "radiant" else req.radiant_picks)
    text, facts = build_explanation(hm[req.hero_id].localized_name, rec,
                                    [hm[e].localized_name for e in enemy if e in hm])
    # LLM-provider: только paraphrase, цифры из facts не меняются (пока fallback)
    return ExplainResponse(hero_id=req.hero_id, explanation=text, facts_used=facts, llm_generated=False)


@app.get("/similar-scenarios")
def similar_scenarios(radiant: str = "", dire: str = "", team: str = "radiant"):
    def _parse(v: str) -> list[int]:
        return [int(x) for x in v.split(",") if x.strip().isdigit()]
    ctx = search_similar(settings.QDRANT_URL, "draft_scenarios", _parse(radiant), _parse(dire), team) \
        if settings.ENABLE_RAG else []
    return {"results": ctx, "rag_enabled": settings.ENABLE_RAG}


@app.exception_handler(HTTPException)
async def _http_exc(_, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
