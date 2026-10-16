"""Объяснения рекомендаций. LLM только перефразирует факты, цифры не меняет.
Без ключа — детерминированный template (llm_generated=False)."""
from __future__ import annotations
from .models import Recommendation


def build_explanation(hero_name: str, rec: Recommendation, enemy_names: list[str]) -> tuple[str, dict]:
    parts = [f"{hero_name}: score {rec.score:.2f}, уверенность {rec.confidence}."]
    for r in rec.reasons:
        if r.type == "matchup":
            parts.append(f"Матчап: {r.summary.lower()} ({r.games_played} игр).")
        elif r.type == "role":
            parts.append(f"Роль: {r.summary.lower()}.")
        elif r.type == "meta":
            parts.append(f"Мета: {r.summary.lower()}.")
    if enemy_names:
        parts.append(f"Против: {', '.join(enemy_names)}.")
    for c in rec.caveats:
        parts.append(f"Оговорка: {c}.")
    parts.append("Матчап — статистическая ассоциация, а не гарантия победы.")
    facts = {"hero_id": rec.hero_id, "score": rec.score, "confidence": rec.confidence,
             "reasons": [r.model_dump() for r in rec.reasons], "caveats": rec.caveats}
    return " ".join(parts), facts
