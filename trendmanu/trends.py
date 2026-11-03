"""Cliente de Google Trends: RSS diario + rising queries de 7 días."""

from __future__ import annotations

import logging
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

from .config import (
    MAX_DAILY_SEEDS,
    MAX_RELATED_TOP_PER_SEED,
    MAX_RISING_PER_SEED,
    Country,
)
from .models import TrendSignal
from .utils import normalize_text

LOGGER = logging.getLogger("trendmanu.trends")

try:  # pytrends-modern es el paquete recomendado en requirements.txt
    from pytrends_modern import TrendReq, TrendsRSS
except ImportError:  # compatibilidad con pytrends clásico
    from pytrends.request import TrendReq  # type: ignore[no-redef]

    TrendsRSS = None  # type: ignore[assignment]


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(element: ET.Element, name: str) -> str:
    for child in element:
        if _local_name(child.tag) == name:
            return (child.text or "").strip()
    return ""


def _parse_traffic(value: Any) -> int:
    if isinstance(value, (int, float)):
        return int(value)
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return int(digits) if digits else 0


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(str(value))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _to_float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").replace(",", "").replace("%", "").strip()
    if text.lower() in {"breakout", "explosión", "explosion"}:
        return 5000.0
    try:
        return float(text)
    except ValueError:
        return default


class GoogleTrendsClient:
    """Obtiene las señales de Google Trends para un país."""

    def __init__(self, country: Country):
        self.country = country
        self._client: Any | None = None

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = TrendReq(
                hl=self.country.language,
                tz=360,
                geo=self.country.region_code,
                timeout=(10, 30),
                retries=2,
                backoff_factor=0.5,
            )
        return self._client

    # ------------------------------------------------------------------
    # Tendencias de las últimas 24 horas
    # ------------------------------------------------------------------
    def fetch_daily(self) -> tuple[list[TrendSignal], list[str]]:
        warnings: list[str] = []
        rows: list[dict[str, Any]] = []

        if TrendsRSS is not None:
            try:
                rss = TrendsRSS(timeout=20)
                rows = rss.get_trends(geo=self.country.region_code) or []
            except Exception as exc:  # noqa: BLE001 - la fuente puede cambiar
                LOGGER.warning("TrendsRSS falló: %s", exc)
                warnings.append(
                    "Google Trends RSS no respondió; se intentó la lectura directa del feed."
                )

        if not rows:
            try:
                rows = self._fetch_daily_fallback()
            except Exception as exc:  # noqa: BLE001
                LOGGER.warning("Fallback RSS falló: %s", exc)
                warnings.append("No fue posible leer las tendencias diarias de Google.")
                return [], warnings

        signals: list[TrendSignal] = []
        seen: set[str] = set()
        for row in rows:
            topic = str(row.get("title", "")).strip()
            key = normalize_text(topic)
            if not topic or not key or key in seen:
                continue
            seen.add(key)

            articles = row.get("articles") or []
            article_titles = []
            for article in articles:
                if isinstance(article, dict):
                    title = article.get("title")
                    if title:
                        article_titles.append(str(title))

            signals.append(
                TrendSignal(
                    topic=topic,
                    signal="daily",
                    source="google",
                    traffic=_parse_traffic(row.get("traffic")),
                    context=" ".join(article_titles)[:600],
                    published_at=_parse_datetime(row.get("pub_date")),
                )
            )

        return signals, warnings

    def _fetch_daily_fallback(self) -> list[dict[str, Any]]:
        """Lee el RSS público sin depender de pytrends."""
        url = f"https://trends.google.com/trending/rss?geo={self.country.region_code}"
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
                )
            },
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = response.read()
        root = ET.fromstring(payload)

        rows: list[dict[str, Any]] = []
        for item in root.iter():
            if _local_name(item.tag) != "item":
                continue
            topic = _child_text(item, "title")
            if not topic:
                continue
            articles = []
            for child in item:
                if _local_name(child.tag) != "news_item":
                    continue
                article_title = _child_text(child, "news_item_title")
                if article_title:
                    articles.append({"title": article_title})
            rows.append(
                {
                    "title": topic,
                    "traffic": _child_text(item, "approx_traffic"),
                    "pub_date": _child_text(item, "pubDate"),
                    "articles": articles,
                }
            )
        return rows

    # ------------------------------------------------------------------
    # Rising queries + queries top de los últimos 7 días
    # ------------------------------------------------------------------
    def fetch_related(
        self, seed: str
    ) -> tuple[list[TrendSignal], list[TrendSignal], str | None]:
        """Devuelve (rising, top) relacionados con un tema semilla."""
        try:
            self.client.build_payload(
                [seed], timeframe="now 7-d", geo=self.country.region_code
            )
            data = self.client.related_queries() or {}
        except Exception as exc:  # noqa: BLE001 - Google puede limitar peticiones
            LOGGER.warning("related_queries falló para %r: %s", seed, exc)
            return [], [], "Google limitó las consultas relacionadas; se muestran menos temas."

        payload = data.get(seed) or {}
        rising_rows = self._dataframe_records(payload.get("rising"))
        top_rows = self._dataframe_records(payload.get("top"))

        rising: list[TrendSignal] = []
        for row in rising_rows[:MAX_RISING_PER_SEED]:
            query = str(row.get("query", "")).strip()
            if not query:
                continue
            rising.append(
                TrendSignal(
                    topic=query,
                    signal="rising",
                    source="google",
                    growth=_to_float(row.get("value")),
                    parent=seed,
                )
            )

        top: list[TrendSignal] = []
        for row in top_rows[:MAX_RELATED_TOP_PER_SEED]:
            query = str(row.get("query", "")).strip()
            if not query:
                continue
            value = _to_float(row.get("value"))
            top.append(
                TrendSignal(
                    topic=query,
                    signal="related_top",
                    source="google",
                    interest=value,
                    weekly_interest=value,
                    parent=seed,
                )
            )

        return rising, top, None

    @staticmethod
    def _dataframe_records(frame: Any) -> list[dict[str, Any]]:
        if frame is None:
            return []
        try:
            if getattr(frame, "empty", False):
                return []
            return frame.to_dict(orient="records")
        except Exception:  # noqa: BLE001
            return []

    # ------------------------------------------------------------------
    # Interés semanal (7 días) para medir impulso sostenido
    # ------------------------------------------------------------------
    def fetch_weekly_interest(
        self, seeds: list[str]
    ) -> tuple[dict[str, dict[str, float]], str | None]:
        seeds = [seed for seed in seeds if seed][:5]
        if not seeds:
            return {}, None

        try:
            self.client.build_payload(
                seeds, timeframe="now 7-d", geo=self.country.region_code
            )
            frame = self.client.interest_over_time()
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("interest_over_time falló: %s", exc)
            return {}, "No se pudo medir el impulso semanal de Google Trends."

        if frame is None or getattr(frame, "empty", True):
            return {}, None

        if "isPartial" in frame.columns:
            frame = frame[frame["isPartial"] == False]  # noqa: E712

        result: dict[str, dict[str, float]] = {}
        for seed in seeds:
            if seed not in frame.columns:
                continue
            series = frame[seed].dropna()
            if series.empty:
                continue
            midpoint = max(1, len(series) // 2)
            first_half = series.iloc[:midpoint]
            second_half = series.iloc[midpoint:]
            first_mean = float(first_half.mean()) if not first_half.empty else 0.0
            second_mean = float(second_half.mean()) if not second_half.empty else 0.0
            growth = 0.0
            if first_mean > 0:
                growth = (second_mean - first_mean) / first_mean * 100.0
            result[seed] = {
                "interest": float(series.mean()),
                "growth": growth,
            }
        return result, None


def fetch_google_trends(country: Country) -> tuple[list[TrendSignal], list[str], int]:
    """Orquesta la recolección completa de señales de Google Trends."""
    client = GoogleTrendsClient(country)
    warnings: list[str] = []

    daily, daily_warnings = client.fetch_daily()
    warnings.extend(daily_warnings)
    if not daily:
        return [], warnings, 0

    daily_sorted = sorted(daily, key=lambda item: item.traffic, reverse=True)
    seeds = [item.topic for item in daily_sorted[:MAX_DAILY_SEEDS]]
    seed_traffic = {item.topic: item.traffic for item in daily_sorted}
    seed_context = {item.topic: item.context for item in daily_sorted}

    # Impulso de 7 días para las semillas principales.
    weekly, weekly_warning = client.fetch_weekly_interest(seeds)
    if weekly_warning:
        warnings.append(weekly_warning)
    for item in daily:
        data = weekly.get(item.topic)
        if data:
            item.weekly_interest = data["interest"]
            item.weekly_growth = data["growth"]

    related_signals: list[TrendSignal] = []
    for index, seed in enumerate(seeds):
        rising, top, warning = client.fetch_related(seed)
        if warning and warning not in warnings:
            warnings.append(warning)
        for signal in rising + top:
            signal.traffic = seed_traffic.get(seed, 0)
            signal.context = seed_context.get(seed, "")
        related_signals.extend(rising)
        related_signals.extend(top)
        if index < len(seeds) - 1:
            time.sleep(0.35)

    return daily + related_signals, warnings, len(daily)
