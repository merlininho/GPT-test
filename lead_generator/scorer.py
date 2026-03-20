"""Motor de score para priorização de leads com base em ICP."""

from __future__ import annotations

from typing import Dict, Iterable

from utils import clean_text


MULTI_SERVICE_KEYWORDS: Iterable[str] = (
    "implante",
    "ortodontia",
    "endodontia",
    "harmonização",
    "estética facial",
    "botox",
    "cirurgia",
    "especialidades",
    "tratamentos",
    "serviços",
    "procedimentos",
)


def has_multiple_services(description: str) -> bool:
    """Detecta indícios de portfólio amplo por palavras-chave no site."""
    lowered = clean_text(description).lower()
    matches = sum(1 for keyword in MULTI_SERVICE_KEYWORDS if keyword in lowered)
    return matches >= 2


def calculate_score(lead: Dict[str, object]) -> int:
    """Calcula um score de 0 a 10 baseado em sinais de maturidade e necessidade."""
    score = 0
    reviews = int(lead.get("avaliacoes", 0) or 0)
    rating = float(lead.get("nota", 0.0) or 0.0)
    has_site = bool(lead.get("possui_site"))
    has_instagram = bool(lead.get("possui_instagram"))
    description = str(lead.get("descricao_site", "") or "")

    if reviews > 50:
        score += 3
    if rating >= 4.5:
        score += 2
    if has_site:
        score += 2
    if has_instagram:
        score += 2
    if has_multiple_services(description):
        score += 3

    if reviews < 10:
        score -= 2
    if not has_site and not has_instagram:
        score -= 3

    return max(0, min(10, score))
