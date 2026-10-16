"""Детерминированный scoring. Владелец: Agent 3.

Score(hero) = w_c*Counter + w_s*Synergy + w_r*RoleFit + w_m*Meta
Counter: сглаженный винрейт против пиков врага, K=50.
Матчап = ассоциация, не причинность. Малые выборки -> low confidence + caveats.
LLM score НЕ меняет — только объясняет.
"""
from dataclasses import dataclass


@dataclass
class HeroRow:
    id: int
    localized_name: str
    roles: list[str]
    name: str = ""  # npc_dota_hero_* (для портретов в UI)


@dataclass
class MatchupRow:
    hero_id: int
    opponent_hero_id: int
    games_played: int
    wins: int


def smoothed_winrate(wins: int, games: int, k: float = 50.0, prior: float = 0.5) -> float:
    if games <= 0:
        return prior
    return (wins + k * prior) / (games + k)


def confidence_for(total_games: int) -> str:
    if total_games >= 400:
        return "high"
    if total_games >= 100:
        return "medium"
    return "low"


def score_candidate(
    hero: HeroRow,
    enemy_picks: list[int],
    matchups_by_opp: dict[int, MatchupRow | None],
    meta_wr: float | None,
    requested_roles: list[str],
    w_c: float = 0.55,
    w_s: float = 0.15,
    w_r: float = 0.15,
    w_m: float = 0.15,
    k: float = 50.0,
) -> tuple[float, str, list[dict], list[str], int]:
    """Возвращает (score, confidence, reasons, caveats, total_games)."""
    reasons: list[dict] = []
    caveats: list[str] = []
    total_games = 0

    # Counter
    if not enemy_picks:
        counter = 0.5
        caveats.append("Нет пиков соперника — контрпик-оценка нейтральна")
    else:
        num, den = 0.0, 0.0
        for opp in enemy_picks:
            m = matchups_by_opp.get(opp)
            if m is None or m.games_played <= 0:
                wr, g = 0.5, 0
            else:
                wr = smoothed_winrate(m.wins, m.games_played, k)
                g = m.games_played
                total_games += g
                reasons.append({
                    "type": "matchup",
                    "against_hero_id": opp,
                    "summary": "Положительная статистика матчапа" if wr >= 0.52 else (
                        "Нейтральная статистика матчапа" if wr >= 0.48 else "Отрицательная статистика матчапа"),
                    "games_played": g,
                })
            w = g if g > 0 else 25.0  # неизвестные матчапы — малый вес
            num += wr * w
            den += w
        counter = num / den if den else 0.5

    # Synergy MVP: заглушка 0.5, честно (не выдаём фиктивную оценку)
    synergy = 0.5

    # RoleFit: только из реальных ролей источника
    if not requested_roles:
        role_fit = 1.0
    else:
        hit = any(r in hero.roles for r in requested_roles)
        role_fit = 1.0 if hit else 0.3
        reasons.append({
            "type": "role",
            "against_hero_id": None,
            "summary": "Соответствует запрошенной роли" if hit else "Не соответствует запрошенной роли",
            "games_played": 0,
        })

    # Meta
    meta = smoothed_winrate(int((meta_wr or 0.5) * 100), 100, k) if meta_wr is not None else 0.5
    if meta_wr is not None:
        reasons.append({"type": "meta", "against_hero_id": None,
                        "summary": "Сильный общий винрейт" if meta_wr >= 0.52 else "Обычный общий винрейт",
                        "games_played": 100})

    score = w_c * counter + w_s * synergy + w_r * role_fit + w_m * meta
    score = max(0.0, min(1.0, round(score, 4)))

    confidence = confidence_for(total_games) if enemy_picks else "low"
    if confidence == "low":
        caveats.append("Размер выборки и патч влияют на надёжность")
    # unknown patch — всегда напоминаем (источник не даёт патч-разбивку в MVP)
    if "Размер выборки и патч влияют на надёжность" not in caveats and total_games < 400:
        caveats.append("Размер выборки и патч влияют на надёжность")
    return score, confidence, reasons, caveats, total_games
