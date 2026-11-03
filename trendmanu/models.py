"""Modelos de datos usados por el pipeline y la interfaz."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TrendSignal:
    """Una aparición de un tema en una fuente de tendencias."""

    topic: str
    signal: str  # daily | rising | related_top | weekly | youtube
    source: str = "google"  # google | youtube
    traffic: int = 0
    growth: float = 0.0
    interest: float = 0.0
    weekly_growth: float = 0.0
    weekly_interest: float = 0.0
    parent: str = ""
    context: str = ""
    published_at: datetime | None = None


@dataclass
class YouTubeMetrics:
    """Métricas de YouTube para un tema (ventana de 7 días)."""

    available: bool = False
    videos_found: int = 0
    total_results: int = 0
    views_7d: int = 0
    avg_views: float = 0.0
    top_video_title: str = ""
    top_video_url: str = ""
    error: str = ""


@dataclass
class Candidate:
    """Tema candidato, ya fusionado entre Google Trends y YouTube."""

    topic: str
    key: str
    sources: set[str] = field(default_factory=set)
    signals: set[str] = field(default_factory=set)
    traffic: int = 0
    growth: float = 0.0
    interest: float = 0.0
    weekly_growth: float = 0.0
    weekly_interest: float = 0.0
    parent: str = ""
    context: str = ""
    published_at: datetime | None = None
    youtube: YouTubeMetrics = field(default_factory=YouTubeMetrics)


@dataclass
class ScoredCandidate:
    """Resultado final del Score de Oportunidad Viral."""

    candidate: Candidate
    score: int
    search_score: float
    traction_score: float
    competition_score: float
    affinity_score: float
    affinity_category: str
    label: str
    label_key: str
    volume: int
    source_label: str


@dataclass
class DashboardData:
    """Datos crudos de una consulta, reutilizables al cambiar filtros."""

    country: str
    candidates: list[Candidate]
    fetched_at: datetime
    warnings: list[str] = field(default_factory=list)
    youtube_enabled: bool = False
    daily_count: int = 0
    youtube_topic_count: int = 0
