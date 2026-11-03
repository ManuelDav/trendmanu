"""Configuración central de TrendManu."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Country:
    code: str
    name: str
    trends_geo: str
    region_code: str
    timezone: str
    language: str = "es"


COUNTRIES: dict[str, Country] = {
    "MX": Country("MX", "México", "MX", "MX", "America/Mexico_City", "es-MX"),
    "AR": Country("AR", "Argentina", "AR", "AR", "America/Argentina/Buenos_Aires", "es-AR"),
    "CO": Country("CO", "Colombia", "CO", "CO", "America/Bogota", "es-CO"),
    "CL": Country("CL", "Chile", "CL", "CL", "America/Santiago", "es-CL"),
}

DEFAULT_COUNTRY = "MX"

# Categorías de afinidad. Las palabras se comparan sin acentos ni mayúsculas.
CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "tecnología": (
        "tecnologia", "inteligencia artificial", "ia", "chatgpt", "openai", "gemini",
        "android", "iphone", "apple", "samsung", "xiaomi", "google", "microsoft",
        "windows", "software", "aplicacion", "app", "startup", "robot", "robotica",
        "gadget", "computadora", "celular", "telefono", "internet", "ciberseguridad",
        "hacker", "nvidia", "procesador", "semiconductor", "spacex", "nasa", "ciencia",
        "innovacion", "elon musk", "meta", "realidad virtual", "vr", "streaming",
    ),
    "finanzas": (
        "finanzas", "dinero", "dolar", "peso mexicano", "tipo de cambio", "inversion",
        "invertir", "bolsa", "acciones", "mercado", "criptomoneda", "bitcoin",
        "ethereum", "economia", "inflacion", "banco", "credito", "deuda", "ahorro",
        "salario", "pension", "pension bienestar", "negocio", "emprender",
        "emprendimiento", "impuestos", "prestamo", "remesas", "nomina",
        "tarjeta de credito", "interes", "rendimiento", "cetes", "afp", "devaluacion",
    ),
    "motivación": (
        "motivacion", "exito", "habitos", "disciplina", "productividad", "mentalidad",
        "superacion", "inspiracion", "autoestima", "metas", "rutina",
        "crecimiento personal", "coaching", "liderazgo", "ansiedad", "felicidad",
        "estoicismo", "constancia", "proposito", "bienestar", "salud mental",
    ),
    "entretenimiento": (
        "pelicula", "peliculas", "serie", "series", "netflix", "disney", "hbo",
        "prime video", "cine", "estreno", "trailer", "musica", "concierto", "album",
        "cantante", "grupo", "actor", "actriz", "famoso", "farandula", "chisme",
        "reality", "television", "programa", "telenovela", "novela", "anime", "manga",
        "videojuego", "gaming", "streamer", "twitch", "tiktok", "influencer",
        "deporte", "futbol", "partido", "seleccion", "liga", "mundial", "boxeo",
        "lucha", "formula 1", "nba", "beisbol", "tenis", "premios", "alfombra roja",
        "boda", "escandalo", "celebridad",
    ),
    "educación": (
        "educacion", "aprender", "curso", "tutorial", "universidad", "escuela",
        "estudiar", "examen", "matematicas", "ciencia", "historia", "idioma", "ingles",
        "programacion", "python", "como hacer", "explicado", "clase", "conocimiento",
        "investigacion", "salud", "medicina", "nutricion", "ejercicio", "receta",
        "cocina", "manualidades", "tips", "guia",
    ),
}

CATEGORIES: tuple[str, ...] = tuple(CATEGORY_KEYWORDS)

SCORE_WEIGHTS = {
    "search": 0.40,
    "traction": 0.30,
    "competition": 0.20,
    "affinity": 0.10,
}

SCORE_LABELS: tuple[tuple[int, str, str], ...] = (
    (80, "🔥 Alta oportunidad", "high"),
    (60, "⚡ Buena oportunidad", "good"),
    (40, "👀 Vigilar", "watch"),
    (0, "❄️ Baja prioridad", "low"),
)

# Términos que no aportan como tema y solo generan ruido.
GENERIC_TERMS: frozenset[str] = frozenset(
    {
        "shorts", "short", "video", "videos", "youtube", "viral", "virales",
        "suscribete", "suscribirse", "subscribe", "like", "likes", "comenta",
        "comparte", "tendencia", "tendencias", "trending", "trend", "2024", "2025",
        "2026", "2027", "musica", "music", "mix", "playlist", "en vivo", "live",
        "noticias", "noticia", "actualidad", "oficial", "nuevo", "nueva", "mejor",
        "mejores", "top", "full", "hd", "4k", "clips", "clip", "canal", "channel",
        "whatsapp", "facebook", "instagram", "twitter", "x", "tiktok", "twitch",
        "mexico", "argentina", "colombia", "chile", "latam", "espanol", "espanol",
    }
)

BLOCKED_TERMS: tuple[str, ...] = (
    "pornografia", "porno", "xxx", "onlyfans", "nudes", "desnudo",
    "sexo explicito", "gore", "snuff",
)

MAX_DAILY_SEEDS = 3
MAX_RISING_PER_SEED = 3
MAX_RELATED_TOP_PER_SEED = 2
MAX_CANDIDATES_FOR_YOUTUBE = 15
YOUTUBE_SEARCH_DAYS = 7
YOUTUBE_MAX_RESULTS = 25
