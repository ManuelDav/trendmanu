"""Utilidades de texto, fechas y formato para TrendManu."""

from __future__ import annotations

import logging
import re
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo

LOGGER = logging.getLogger("trendmanu")


def configure_logging() -> None:
    """Configura logging una sola vez, sin ruido de librerías externas."""
    if logging.getLogger().handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    for noisy in ("urllib3", "googleapiclient", "pytrends_modern", "requests"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def normalize_text(text: str) -> str:
    """Minúsculas, sin acentos y con espacios simples."""
    decomposed = unicodedata.normalize("NFD", (text or "").lower())
    without_accents = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    cleaned = re.sub(r"[^a-z0-9ñ]+", " ", without_accents)
    return re.sub(r"\s+", " ", cleaned).strip()


def contains_keyword(text: str, keyword: str) -> bool:
    """Busca una palabra o frase completa dentro de un texto normalizado."""
    norm_text = f" {normalize_text(text)} "
    norm_kw = normalize_text(keyword)
    if not norm_kw:
        return False
    if " " in norm_kw:
        return f" {norm_kw} " in norm_text
    return re.search(rf"\b{re.escape(norm_kw)}\b", norm_text) is not None


def same_topic(a: str, b: str) -> bool:
    """Compara dos temas permitiendo coincidencias parciales razonables."""
    na, nb = normalize_text(a), normalize_text(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    short, long = sorted((na, nb), key=len)
    if len(short) < 5:
        return False
    if short not in long:
        return False
    # "sheinbaum" dentro de "claudia sheinbaum" sí; "paris" dentro de
    # "paris open" también. Evitamos frases demasiado cortas o genéricas.
    return len(short.split()) >= 2 or len(short) / max(len(long), 1) >= 0.50


def display_topic(topic: str) -> str:
    """Presenta temas en minúscula con formato de título legible."""
    topic = re.sub(r"\s+", " ", (topic or "").strip())
    if not topic:
        return topic
    # Si la fuente ya trae mayúsculas mixtas (ChatGPT, iPhone), las respetamos.
    if any(ch.isupper() for ch in topic):
        return topic
    title = topic.title()
    small_words = {"de", "del", "la", "las", "el", "los", "y", "e", "en", "para",
                   "con", "por", "a", "al", "que", "vs", "o", "u"}
    words = title.split(" ")
    for i in range(1, len(words)):
        if words[i].lower() in small_words:
            words[i] = words[i].lower()
    return " ".join(words)


def format_int(value: int | float) -> str:
    """Formatea enteros con separador de miles latinoamericano."""
    return f"{int(round(value)):,}".replace(",", ".")


def format_volume(value: int | float) -> str:
    """Formatea un volumen estimado de forma compacta en español."""
    value = max(0, int(round(value)))
    if value == 0:
        return "—"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f} M".replace(".", ",")
    if value >= 1_000:
        decimals = 0 if value >= 100_000 else 1
        return f"{value / 1_000:.{decimals}f} mil".replace(".", ",")
    return str(value)


def format_datetime(value: datetime, timezone: str) -> str:
    """Convierte un datetime a la zona del país y lo muestra en formato corto."""
    try:
        local = value.astimezone(ZoneInfo(timezone))
    except Exception:
        local = value
    return local.strftime("%d/%m/%Y · %H:%M")


def today_label(timezone: str) -> str:
    """Devuelve 'martes, 3 de noviembre de 2026' en la zona indicada."""
    now = datetime.now(ZoneInfo(timezone))
    days = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
    months = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
              "agosto", "septiembre", "octubre", "noviembre", "diciembre")
    label = f"{days[now.weekday()]}, {now.day} de {months[now.month - 1]} de {now.year}"
    return label[0].upper() + label[1:]


def youtube_search_url(topic: str) -> str:
    """URL de búsqueda del tema en YouTube."""
    from urllib.parse import quote_plus

    return f"https://www.youtube.com/results?search_query={quote_plus(topic)}"
