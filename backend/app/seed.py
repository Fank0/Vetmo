"""Seed-данные: реальные ID/имена/роли Dota 2 (проверяемы по OpenDota /heroes).
Матчапы — синтетические, помечены source='seed', только чтобы UI/API работали
без БД и сети. Прод-данные приходят из loader.py (source='opendota').
"""
from datetime import datetime, timezone

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")

SEED_HEROES: list[dict] = [
    {"id": 1, "name": "npc_dota_hero_antimage", "localized_name": "Anti-Mage", "roles": ["Carry", "Escape", "Nuker"], "updated_at": NOW},
    {"id": 2, "name": "npc_dota_hero_axe", "localized_name": "Axe", "roles": ["Initiator", "Durable", "Disabler"], "updated_at": NOW},
    {"id": 3, "name": "npc_dota_hero_bane", "localized_name": "Bane", "roles": ["Support", "Disabler", "Nuker"], "updated_at": NOW},
    {"id": 4, "name": "npc_dota_hero_bloodseeker", "localized_name": "Bloodseeker", "roles": ["Carry", "Disabler", "Nuker"], "updated_at": NOW},
    {"id": 5, "name": "npc_dota_hero_crystal_maiden", "localized_name": "Crystal Maiden", "roles": ["Support", "Disabler", "Nuker"], "updated_at": NOW},
    {"id": 6, "name": "npc_dota_hero_drow_ranger", "localized_name": "Drow Ranger", "roles": ["Carry", "Disabler", "Pusher"], "updated_at": NOW},
    {"id": 7, "name": "npc_dota_hero_earthshaker", "localized_name": "Earthshaker", "roles": ["Support", "Initiator", "Disabler"], "updated_at": NOW},
    {"id": 8, "name": "npc_dota_hero_juggernaut", "localized_name": "Juggernaut", "roles": ["Carry", "Pusher", "Escape"], "updated_at": NOW},
    {"id": 9, "name": "npc_dota_hero_mirana", "localized_name": "Mirana", "roles": ["Carry", "Support", "Escape"], "updated_at": NOW},
    {"id": 11, "name": "npc_dota_hero_nevermore", "localized_name": "Shadow Fiend", "roles": ["Carry", "Nuker"], "updated_at": NOW},
    {"id": 12, "name": "npc_dota_hero_morphling", "localized_name": "Morphling", "roles": ["Carry", "Escape", "Durable"], "updated_at": NOW},
    {"id": 23, "name": "npc_dota_hero_kunkka", "localized_name": "Kunkka", "roles": ["Carry", "Support", "Disabler"], "updated_at": NOW},
]

# (hero_id, opponent_id) -> (wins, games). source='seed'.
SEED_MATCHUPS: dict[tuple[int, int], tuple[int, int]] = {
    (7, 1): (140, 250), (7, 8): (120, 220), (2, 1): (160, 280), (2, 6): (150, 260),
    (5, 8): (60, 200), (3, 8): (130, 240), (8, 6): (155, 290), (11, 5): (170, 300),
    (1, 6): (165, 310), (23, 8): (145, 270), (12, 2): (110, 230), (9, 5): (125, 235),
    (4, 12): (135, 255), (6, 5): (150, 280),
}

SEED_META: dict[int, float] = {1: 0.52, 2: 0.53, 5: 0.49, 7: 0.54, 8: 0.55, 11: 0.51, 23: 0.52, 6: 0.50, 12: 0.53, 9: 0.50, 3: 0.51, 4: 0.49}
