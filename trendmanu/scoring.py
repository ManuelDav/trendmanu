"""Cálculo del Score de Oportunidad Viral (0–100)."""

from __future__ import annotations

import math

from .config import (
    BLOCKED_TERMS,
    CATEGORY_KEYWORDS,
    SCORE_LABELS,
    SCORE_WEIGHTS,
)
from .models import Candidate, ScoredCandidate
from .utils import contains_keyword, normalize_text


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _log_ratio(value: float, ceiling: float) -> float:
    """Escala logarítmica 0–100 para valores con cola larga."""
    if value <= 0:
        return 0.0
    return clamp(math.log10(value + 1) / math.log10(ceiling + 1) * 100)


def search_score(candidate: Candidate) -> float:
    """40 % del score: velocidad de búsqueda en Google Trends."""
    signals = candidate.signals
    base = 35.0

    if "rising" in signals:
        # Las rising queries parten con ventaja, como pide la metodología.
        growth = max(candidate.growth, 1.0)
        base = 86.0 + min(14.0, math.log10(growth + 1) * 3.2)
    elif "daily" in signals:
        traffic = max(candidate.traffic, 1)
        base = 56.0 + min(26.0, math.log10(traffic + 1) * 7.0)
    elif "related_top" in signals:
        interest = max(candidate.interest, 1.0)
        base = 52.0 + min(24.0, interest / 100.0 * 24.0)
    elif "weekly" in signals:
        base = 45.0 + min(25.0, candidate.weekly_interest / 100.0 * 25.0)
    elif "youtube" in signals:
        base = 38.0

    # Impulso sostenido de los últimos 7 días (sube o baja ligeramente).
    if candidate.weekly_growth > 0:
        base += min(8.0, candidate.weekly_growth / 25.0)
    elif candidate.weekly_growth < -20:
        base -= min(8.0, abs(candidate.weekly_growth) / 25.0)

    return clamp(base)


def traction_score(candidate: Candidate) -> float:
    """30 % del score: vistas acumuladas por videos publicados en 7 días."""
    if not candidate.youtube.available:
        return 50.0  # neutral si no hay API key o se agotó la cuota
    return _log_ratio(candidate.youtube.views_7d, 5_000_000)


def competition_score(candidate: Candidate) -> float:
    """20 % del score: menos videos recientes = mejor oportunidad."""
    if not candidate.youtube.available:
        return 50.0
    videos = max(candidate.youtube.total_results, candidate.youtube.videos_found)
    if videos <= 0:
        return 100.0
    return clamp(100.0 - _log_ratio(videos, 100_000))


def affinity_score(
    candidate: Candidate, selected_categories: list[str] | tuple[str, ...]
) -> tuple[float, str]:
    """10 % del score: cercanía con las categorías elegidas en la barra lateral."""
    if not selected_categories:
        return 50.0, "Sin filtro"

    text = f"{candidate.topic} {candidate.context}"
    best_score = 15.0
    best_category = "General"

    for category in selected_categories:
        keywords = CATEGORY_KEYWORDS.get(category, ())
        matches = sum(1 for keyword in keywords if contains_keyword(text, keyword))
        if matches:
            score = 45.0 + min(55.0, (matches - 1) * 15.0)
            if score > best_score:
                best_score = score
                best_category = category

    return best_score, best_category


def label_for(score: int) -> tuple[str, str]:
    for threshold, label, key in SCORE_LABELS:
        if score >= threshold:
            return label, key
    return SCORE_LABELS[-1][1], SCORE_LABELS[-1][2]


def estimate_volume(candidate: Candidate) -> int:
    """Estimación de búsquedas a partir del tráfico de Google Trends.

    Google Trends no publica volúmenes absolutos, por lo que partimos del
    ``approx_traffic`` del RSS diario y lo ajustamos con el crecimiento o la
    participación de la query. La UI siempre lo marca como estimado.
    """
    traffic = max(candidate.traffic, 0)
    if traffic:
        if "rising" in candidate.signals:
            factor = max(1.0, math.log10(max(candidate.growth, 1.0) + 1.0))
            return int(min(traffic * factor, 1_000_000))
        if "related_top" in candidate.signals:
            share = clamp(candidate.interest / 100.0, 0.1, 1.5)
            return int(min(traffic * share, 1_000_000))
        return traffic
    if candidate.youtube.views_7d:
        return int(min(candidate.youtube.views_7d / 12, 1_000_000))
    return 0


def source_label(candidate: Candidate) -> str:
    has_google = "google" in candidate.sources
    has_youtube = "youtube" in candidate.sources
    if has_google and has_youtube:
        return "Ambas"
    if has_youtube:
        return "YouTube"
    return "Google"


def is_blocked(topic: str) -> bool:
    norm = normalize_text(topic)
    return any(term in norm for term in BLOCKED_TERMS)


def score_candidate(
    candidate: Candidate, selected_categories: list[str] | tuple[str, ...]
) -> ScoredCandidate:
    search = search_score(candidate)
    traction = traction_score(candidate)
    competition = competition_score(candidate)
    affinity, category = affinity_score(candidate, selected_categories)

    total = (
        SCORE_WEIGHTS["search"] * search
        + SCORE_WEIGHTS["traction"] * traction
        + SCORE_WEIGHTS["competition"] * competition
        + SCORE_WEIGHTS["affinity"] * affinity
    )
    score = int(round(clamp(total)))
    label, label_key = label_for(score)

    return ScoredCandidate(
        candidate=candidate,
        score=score,
        search_score=round(search, 1),
        traction_score=round(traction, 1),
        competition_score=round(competition, 1),
        affinity_score=round(affinity, 1),
        affinity_category=category,
        label=label,
        label_key=label_key,
        volume=estimate_volume(candidate),
        source_label=source_label(candidate),
    )


def rank_candidates(
    candidates: list[Candidate],
    selected_categories: list[str] | tuple[str, ...],
    excluded_terms: list[str] | None = None,
    limit: int = 10,
) -> list[ScoredCandidate]:
    """Filtra, puntúa y ordena los temas del día."""
    excluded = [term for term in (excluded_terms or []) if normalize_text(term)]
    ranked: list[ScoredCandidate] = []

    for candidate in candidates:
        norm_topic = normalize_text(candidate.topic)
        if not norm_topic or is_blocked(candidate.topic):
            continue
        if any(normalize_text(term) in norm_topic for term in excluded):
            continue
        ranked.append(score_candidate(candidate, selected_categories))

    ranked.sort(
        key=lambda item: (
            item.score,
            item.candidate.youtube.views_7d,
            item.volume,
        ),
        reverse=True,
    )
    return ranked[:limit]
