"""Контракты Hero/Matchup/Draft Request/Response. Владелец: Agent 3, freeze: Agent 1."""
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class Hero(BaseModel):
    id: int
    name: str
    localized_name: str
    roles: list[str] = []
    updated_at: str = ""


class Matchup(BaseModel):
    hero_id: int
    opponent_hero_id: int
    patch: str = "unknown"
    games_played: int = 0
    wins: int = 0
    win_rate: float | None = None
    source: str = "opendota"
    updated_at: str = ""


class DraftRequest(BaseModel):
    radiant_picks: list[int] = []
    dire_picks: list[int] = []
    radiant_bans: list[int] = []
    dire_bans: list[int] = []
    team_to_pick: Literal["radiant", "dire"] = "radiant"
    requested_roles: list[str] = []
    limit: int = Field(default=10, ge=1, le=25)

    @field_validator("radiant_picks", "dire_picks", "radiant_bans", "dire_bans")
    @classmethod
    def _positive(cls, v: list[int]) -> list[int]:
        for x in v:
            if not isinstance(x, int) or x <= 0:
                raise ValueError(f"hero id must be int > 0, got {x!r}")
        if len(v) != len(set(v)):
            raise ValueError(f"duplicate hero id in {v}")
        return v

    def all_selected(self) -> set[int]:
        return set(self.radiant_picks + self.dire_picks + self.radiant_bans + self.dire_bans)

    def validate_no_overlap(self) -> None:
        groups = [self.radiant_picks, self.dire_picks, self.radiant_bans, self.dire_bans]
        seen: dict[int, int] = {}
        for i, g in enumerate(groups):
            for h in g:
                if h in seen:
                    raise ValueError(f"hero id {h} appears in multiple groups")
                seen[h] = i


class Reason(BaseModel):
    type: Literal["matchup", "role", "meta", "synergy"]
    against_hero_id: int | None = None
    summary: str
    games_played: int = 0


class Recommendation(BaseModel):
    hero_id: int
    score: float
    confidence: Literal["high", "medium", "low"]
    reasons: list[Reason] = []
    caveats: list[str] = []


class DraftResponse(BaseModel):
    recommendations: list[Recommendation]
    data_updated_at: str
    rag_context: list[dict] = []
    meta: dict = {}


class ExplainRequest(DraftRequest):
    hero_id: int


class ExplainResponse(BaseModel):
    hero_id: int
    explanation: str
    facts_used: dict
    llm_generated: bool = False
