"""Pipeline: recolecta, fusiona y enriquece los temas del día."""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone

from .config import (
    COUNTRIES,
    MAX_CANDIDATES_FOR_YOUTUBE,
    Country,
)
from .models import Candidate, DashboardData, TrendSignal
from .scoring import rank_candidates
from .trends import fetch_google_trends
from .utils import normalize_text, same_topic
from .youtube import QuotaExceededError, YouTubeClient, YouTubeTopic

LOGGER = logging.getLogger("trendmanu.pipeline")


def _merge_google_signals(signals: list[TrendSignal]) -> list[Candidate]:
    """Fusiona señales que apuntan al mismo tema."""
    by_key: dict[str, Candidate] = {}

    for signal in signals:
        key = normalize_text(signal.topic)
        if not key:
            continue

        existing = by_key.get(key)
        if existing is None:
            signals_found = {signal.signal}
            if signal.weekly_interest > 0 or signal.signal == "related_top":
                signals_found.add("weekly")
            by_key[key] = Candidate(
                topic=signal.topic,
                key=key,
                sources={signal.source},
                signals=signals_found,
                traffic=signal.traffic,
                growth=signal.growth,
                interest=signal.interest,
                weekly_growth=signal.weekly_growth,
                weekly_interest=signal.weekly_interest,
                parent=signal.parent,
                context=signal.context,
                published_at=signal.published_at,
            )
            continue

        existing.signals.add(signal.signal)
        if signal.weekly_interest > 0 or signal.signal == "related_top":
            existing.signals.add("weekly")
        existing.sources.add(signal.source)
        existing.traffic = max(existing.traffic, signal.traffic)
        existing.growth = max(existing.growth, signal.growth)
        existing.interest = max(existing.interest, signal.interest)
        existing.weekly_growth = signal.weekly_growth or existing.weekly_growth
        existing.weekly_interest = signal.weekly_interest or existing.weekly_interest
        existing.parent = existing.parent or signal.parent
        if signal.context and signal.context not in existing.context:
            existing.context = f"{existing.context} {signal.context}".strip()[:900]
        if signal.published_at and existing.published_at is None:
            existing.published_at = signal.published_at

    return list(by_key.values())


def _merge_youtube_topics(
    candidates: list[Candidate], topics: list[YouTubeTopic]
) -> int:
    """Integra temas detectados en YouTube y marca la fuente 'Ambas'."""
    added = 0
    for topic in topics:
        match = next(
            (candidate for candidate in candidates if same_topic(candidate.topic, topic.topic)),
            None,
        )
        if match is not None:
            match.sources.add("youtube")
            if topic.context and topic.context not in match.context:
                match.context = f"{match.context} {topic.context}".strip()[:900]
            continue

        key = normalize_text(topic.topic)
        if not key:
            continue
        candidates.append(
            Candidate(
                topic=topic.topic,
                key=key,
                sources={"youtube"},
                signals={"youtube"},
                context=topic.context,
            )
        )
        added += 1
    return added


def _priority(candidate: Candidate) -> float:
    if "rising" in candidate.signals:
        base = 100.0
    elif "daily" in candidate.signals:
        base = 80.0
    elif "related_top" in candidate.signals:
        base = 60.0
    elif "youtube" in candidate.signals:
        base = 40.0
    else:
        base = 20.0

    base += min(20.0, math.log10(max(candidate.traffic, 0) + 1) * 5.0)
    if "youtube" in candidate.sources:
        base += 4.0
    return base


def _select_for_youtube(candidates: list[Candidate], limit: int) -> list[Candidate]:
    """Elige candidatos para no gastar cuota en temas irrelevantes."""
    ordered = sorted(candidates, key=_priority, reverse=True)
    selected: list[Candidate] = []
    seen: set[str] = set()

    # Garantizamos que YouTube aporte temas propios (si los hay).
    youtube_only = [
        candidate
        for candidate in ordered
        if candidate.sources == {"youtube"}
    ]
    for candidate in youtube_only[:3]:
        selected.append(candidate)
        seen.add(candidate.key)

    for candidate in ordered:
        if len(selected) >= limit:
            break
        if candidate.key in seen:
            continue
        selected.append(candidate)
        seen.add(candidate.key)

    return selected


def build_dashboard_data(country_code: str, youtube_api_key: str) -> DashboardData:
    """Consulta las fuentes y deja los temas listos para puntuar."""
    country: Country = COUNTRIES.get(country_code, COUNTRIES["MX"])
    warnings: list[str] = []

    LOGGER.info("Consultando Google Trends para %s", country.code)
    signals, trend_warnings, daily_count = fetch_google_trends(country)
    warnings.extend(trend_warnings)

    candidates = _merge_google_signals(signals)
    youtube_enabled = bool(youtube_api_key.strip())
    youtube_topic_count = 0

    if youtube_enabled:
        client = YouTubeClient(
            api_key=youtube_api_key,
            region_code=country.region_code,
            language=country.language,
        )
        LOGGER.info("Consultando temas populares de YouTube %s", country.code)
        trending_topics = client.fetch_trending_topics()
        youtube_topic_count = len(trending_topics)
        if client.last_error:
            warnings.append(
                f"{client.last_error} Revisa YOUTUBE_API_KEY y la cuota; "
                "las métricas de YouTube quedan en modo neutral."
            )
        else:
            _merge_youtube_topics(candidates, trending_topics)

            candidates = _select_for_youtube(candidates, MAX_CANDIDATES_FOR_YOUTUBE)
            LOGGER.info("Midiendo competencia/tracción de %d temas", len(candidates))

            for candidate in candidates:
                try:
                    candidate.youtube = client.search_topic(candidate.topic)
                except QuotaExceededError:
                    warnings.append(
                        "Se agotó la cuota diaria de YouTube Data API. "
                        "Los temas sin medir usan valores neutrales."
                    )
                    break
                except Exception as exc:  # noqa: BLE001
                    LOGGER.warning("YouTube falló para %r: %s", candidate.topic, exc)
                    candidate.youtube.error = "No se pudo consultar YouTube."

                if client.last_error:
                    warnings.append(
                        f"{client.last_error} Las métricas restantes de YouTube "
                        "quedan en modo neutral."
                    )
                    break
    else:
        warnings.append(
            "Falta YOUTUBE_API_KEY: se muestran tendencias de Google y las "
            "métricas de YouTube usan valores neutrales."
        )

    if not candidates:
        warnings.append(
            "No se encontraron temas candidatos. Revisa tu conexión o pulsa "
            "«Actualizar tendencias ahora»."
        )

    return DashboardData(
        country=country.code,
        candidates=candidates,
        fetched_at=datetime.now(timezone.utc),
        warnings=warnings,
        youtube_enabled=youtube_enabled,
        daily_count=daily_count,
        youtube_topic_count=youtube_topic_count,
    )


def rank_dashboard(
    data: DashboardData,
    selected_categories: list[str],
    excluded_terms: list[str],
    limit: int = 10,
):
    return rank_candidates(
        data.candidates,
        selected_categories=selected_categories,
        excluded_terms=excluded_terms,
        limit=limit,
    )
