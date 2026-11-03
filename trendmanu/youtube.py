"""Cliente de YouTube Data API v3."""

from __future__ import annotations

import logging
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import GENERIC_TERMS, YOUTUBE_MAX_RESULTS, YOUTUBE_SEARCH_DAYS
from .models import YouTubeMetrics
from .utils import normalize_text

LOGGER = logging.getLogger("trendmanu.youtube")

EXTRA_GENERIC_TAGS = {
    "shorts", "short", "viral", "virales", "tendencia", "trending", "youtube",
    "video", "videos", "suscribete", "subscribe", "like", "comparte", "comenta",
    "music", "musica", "official", "oficial", "new", "nuevo", "nueva", "full",
    "hd", "4k", "2025", "2026", "2027", "live", "envivo", "clip", "clips",
    "mexico", "argentina", "colombia", "chile", "latam", "espanol", "español",
}

STOPWORDS = {
    "para", "como", "este", "esta", "esto", "esos", "esas", "pero", "porque",
    "cuando", "donde", "desde", "hasta", "entre", "sobre", "tambien", "solo",
    "todo", "toda", "todos", "todas", "hace", "hacer", "tiene", "tienen",
    "despues", "antes", "ahora", "aqui", "alla", "muy", "mas", "menos", "sin",
    "con", "por", "del", "las", "los", "una", "unos", "unas", "que", "sus",
    "the", "and", "for", "with", "this", "that", "from", "your", "you", "new",
}


class QuotaExceededError(RuntimeError):
    """La cuota diaria de YouTube Data API se agotó."""


@dataclass
class YouTubeTopic:
    topic: str
    mentions: int
    context: str = ""


class YouTubeClient:
    def __init__(
        self,
        api_key: str,
        region_code: str,
        language: str = "es",
        service: Any | None = None,
    ):
        self.api_key = api_key
        self.region_code = region_code
        self.language = language
        self._service = service
        self.last_error = ""

    @property
    def service(self) -> Any:
        if self._service is None:
            self._service = build(
                "youtube",
                "v3",
                developerKey=self.api_key,
                cache_discovery=False,
            )
        return self._service

    # ------------------------------------------------------------------
    # Temas que ya están sonando en YouTube
    # ------------------------------------------------------------------
    def fetch_trending_topics(self, limit: int = 12) -> list[YouTubeTopic]:
        try:
            response = (
                self.service.videos()
                .list(
                    part="snippet",
                    chart="mostPopular",
                    regionCode=self.region_code,
                    maxResults=25,
                )
                .execute()
            )
        except HttpError as exc:
            LOGGER.warning("YouTube mostPopular falló: %s", exc)
            self.last_error = "YouTube rechazó la consulta (API key o cuota)."
            return []
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("YouTube mostPopular falló: %s", exc)
            self.last_error = "No se pudo conectar con YouTube."
            return []

        counts: Counter[str] = Counter()
        labels: dict[str, str] = {}
        contexts: dict[str, list[str]] = {}

        for item in response.get("items", []):
            snippet = item.get("snippet", {}) or {}
            title = str(snippet.get("title", "") or "")
            description = str(snippet.get("description", "") or "")

            raw_tags = list(snippet.get("tags", []) or [])
            raw_tags += re.findall(r"#([\wáéíóúñüÁÉÍÓÚÑÜ]+)", f"{title} {description}")

            for raw_tag in raw_tags:
                tag = re.sub(r"^#+", "", str(raw_tag)).strip()
                key = normalize_text(tag)
                if not self._valid_tag(key, tag):
                    continue
                counts[key] += 1
                labels.setdefault(key, tag)
                if len(contexts.setdefault(key, [])) < 2:
                    contexts[key].append(title)

        # Si los tags no alcanzan, rescatamos frases de los títulos.
        if len(counts) < 6:
            for item in response.get("items", []):
                title = str((item.get("snippet", {}) or {}).get("title", "") or "")
                for phrase in self._title_phrases(title):
                    key = normalize_text(phrase)
                    if not self._valid_tag(key, phrase):
                        continue
                    counts[key] += 1
                    labels.setdefault(key, phrase)
                    if len(contexts.setdefault(key, [])) < 2:
                        contexts[key].append(title)

        topics: list[YouTubeTopic] = []
        for key, mentions in counts.most_common(limit):
            topics.append(
                YouTubeTopic(
                    topic=labels[key],
                    mentions=mentions,
                    context=" ".join(contexts.get(key, [])),
                )
            )
        return topics

    @staticmethod
    def _valid_tag(key: str, tag: str) -> bool:
        if not key or len(key) < 3 or len(key) > 45:
            return False
        if key in GENERIC_TERMS or key in EXTRA_GENERIC_TAGS:
            return False
        if key.isdigit() or "http" in key:
            return False
        if len(tag.split()) > 6:
            return False
        return True

    @staticmethod
    def _title_phrases(title: str) -> list[str]:
        clean = re.sub(r"#\w+", " ", title)
        clean = re.sub(r"[^\wáéíóúñüÁÉÍÓÚÑÜ\s]", " ", clean)
        tokens = [token for token in clean.split() if len(token) >= 4]
        tokens = [token for token in tokens if normalize_text(token) not in STOPWORDS]
        phrases = []
        for index in range(len(tokens) - 1):
            phrase = f"{tokens[index]} {tokens[index + 1]}"
            if 8 <= len(phrase) <= 45:
                phrases.append(phrase)
        return phrases[:3]

    # ------------------------------------------------------------------
    # Competencia y tracción de un tema en los últimos 7 días
    # ------------------------------------------------------------------
    def search_topic(self, topic: str) -> YouTubeMetrics:
        published_after = (
            datetime.now(timezone.utc) - timedelta(days=YOUTUBE_SEARCH_DAYS)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        try:
            search_response = (
                self.service.search()
                .list(
                    part="snippet",
                    q=topic,
                    type="video",
                    order="viewCount",
                    maxResults=YOUTUBE_MAX_RESULTS,
                    regionCode=self.region_code,
                    relevanceLanguage=self.language,
                    publishedAfter=published_after,
                    safeSearch="none",
                )
                .execute()
            )
        except HttpError as exc:
            if self._is_quota_error(exc):
                raise QuotaExceededError("Cuota diaria de YouTube Data API agotada") from exc
            LOGGER.warning("search.list falló para %r: %s", topic, exc)
            self.last_error = "YouTube rechazó la búsqueda (API key o cuota)."
            return YouTubeMetrics(available=False, error="YouTube no respondió para este tema.")
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("search.list falló para %r: %s", topic, exc)
            self.last_error = "No se pudo conectar con YouTube."
            return YouTubeMetrics(available=False, error="YouTube no respondió para este tema.")

        page_info = search_response.get("pageInfo", {}) or {}
        total_results = int(page_info.get("totalResults", 0) or 0)
        video_ids = [
            item.get("id", {}).get("videoId")
            for item in search_response.get("items", [])
            if item.get("id", {}).get("videoId")
        ]

        if not video_ids:
            return YouTubeMetrics(
                available=True,
                videos_found=0,
                total_results=total_results,
            )

        try:
            videos_response = (
                self.service.videos()
                .list(
                    part="snippet,statistics",
                    id=",".join(video_ids),
                    maxResults=50,
                )
                .execute()
            )
        except HttpError as exc:
            if self._is_quota_error(exc):
                raise QuotaExceededError("Cuota diaria de YouTube Data API agotada") from exc
            LOGGER.warning("videos.list falló para %r: %s", topic, exc)
            return YouTubeMetrics(
                available=True,
                videos_found=len(video_ids),
                total_results=total_results,
                error="No se pudieron leer las estadísticas de los videos.",
            )

        total_views = 0
        top_title = ""
        top_url = ""
        top_views = -1
        fetched = 0
        for item in videos_response.get("items", []):
            stats = item.get("statistics", {}) or {}
            if not stats:
                continue
            fetched += 1
            views = int(stats.get("viewCount", 0) or 0)
            total_views += views
            if views > top_views:
                top_views = views
                snippet = item.get("snippet", {}) or {}
                top_title = str(snippet.get("title", "") or "")
                top_url = f"https://www.youtube.com/watch?v={item.get('id', '')}"

        return YouTubeMetrics(
            available=True,
            videos_found=fetched or len(video_ids),
            total_results=total_results,
            views_7d=total_views,
            avg_views=(total_views / fetched) if fetched else 0.0,
            top_video_title=top_title,
            top_video_url=top_url,
        )

    @staticmethod
    def _is_quota_error(exc: HttpError) -> bool:
        try:
            content = exc.content.decode("utf-8") if isinstance(exc.content, bytes) else str(exc.content)
        except Exception:  # noqa: BLE001
            content = str(exc)
        return "quotaExceeded" in content or "dailyLimitExceeded" in content
