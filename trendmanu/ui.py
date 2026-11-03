"""Componentes visuales y estilos de TrendManu."""

from __future__ import annotations

import html

import streamlit as st

from .config import CATEGORIES
from .models import DashboardData, ScoredCandidate
from .utils import (
    display_topic,
    format_datetime,
    format_int,
    format_volume,
    today_label,
    youtube_search_url,
)

CSS = """
<style>
:root {
  --tm-bg: #0a0f14;
  --tm-panel: #111820;
  --tm-panel-2: #151e28;
  --tm-border: rgba(255, 255, 255, 0.08);
  --tm-orange: #FF6B35;
  --tm-green: #39FF14;
  --tm-text: #EAF0F6;
  --tm-muted: #8A99A8;
  --tm-good: #FFC857;
  --tm-watch: #5AC8FA;
  --tm-low: #748291;
}

html, body, [class*="css"] {
  font-family: Inter, "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
  background:
    radial-gradient(1100px 500px at 85% -10%, rgba(255, 107, 53, 0.13), transparent 60%),
    radial-gradient(800px 420px at 8% 0%, rgba(57, 255, 20, 0.06), transparent 55%),
    var(--tm-bg);
  color: var(--tm-text);
}

[data-testid="stHeader"] { background: transparent; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
.block-container { max-width: 1180px; padding-top: 2.1rem; padding-bottom: 2.5rem; }

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0c1219 0%, #0a0f14 100%);
  border-right: 1px solid var(--tm-border);
}
[data-testid="stSidebar"] .block-container { padding-top: 1.4rem; }

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: var(--tm-text); letter-spacing: -0.02em; }

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p { color: #C6D1DC; }

.stButton > button {
  border-radius: 12px;
  border: 1px solid rgba(255, 107, 53, 0.45);
  background: linear-gradient(135deg, #FF6B35, #FF8A5C);
  color: #140B07;
  font-weight: 800;
  letter-spacing: 0.01em;
  padding: 0.62rem 1rem;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.stButton > button:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 26px rgba(255, 107, 53, 0.25);
  color: #140B07;
  border-color: rgba(255, 107, 53, 0.8);
}
.stButton > button:focus { color: #140B07; }

div[data-baseweb="select"] > div,
.stTextInput input {
  background: var(--tm-panel) !important;
  border-color: var(--tm-border) !important;
  color: var(--tm-text) !important;
  border-radius: 10px !important;
}
[data-testid="stMarkdownContainer"] a { color: var(--tm-orange); }

.tm-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 1.5rem;
  padding: 1.3rem 1.4rem 1.4rem;
  border: 1px solid var(--tm-border);
  border-radius: 22px;
  background:
    linear-gradient(135deg, rgba(255, 107, 53, 0.10), transparent 45%),
    linear-gradient(180deg, rgba(255,255,255,0.035), rgba(255,255,255,0.008));
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.28);
  margin-bottom: 1rem;
}
.tm-brand { display: flex; gap: 1rem; align-items: center; }
.tm-mark {
  width: 54px; height: 54px;
  display: grid; place-items: center;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(255,107,53,0.24), rgba(57,255,20,0.12));
  border: 1px solid rgba(255, 107, 53, 0.38);
  font-size: 1.55rem;
  box-shadow: inset 0 0 22px rgba(255,107,53,0.10);
}
.tm-eyebrow {
  font-size: 0.68rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--tm-green);
  font-weight: 800;
  margin-bottom: 0.15rem;
}
.tm-hero h1 {
  margin: 0;
  font-size: clamp(1.8rem, 4vw, 2.7rem);
  line-height: 1.05;
  letter-spacing: -0.045em;
  color: #FFFFFF;
  font-weight: 900;
}
.tm-hero h1 span { color: var(--tm-orange); font-weight: 800; }
.tm-tagline { margin: 0.45rem 0 0; color: var(--tm-muted); font-size: 0.95rem; }

.tm-datebox { text-align: right; min-width: 230px; }
.tm-date-label {
  font-size: 0.62rem; letter-spacing: 0.2em; color: var(--tm-muted); font-weight: 800;
}
.tm-date { font-size: 1rem; font-weight: 800; color: var(--tm-text); margin: 0.15rem 0 0.35rem; }
.tm-live { font-size: 0.75rem; color: #B7C4D1; display: flex; justify-content: flex-end; align-items: center; gap: 0.4rem; }
.tm-dot {
  width: 7px; height: 7px; border-radius: 50%; background: var(--tm-green);
  box-shadow: 0 0 0 0 rgba(57,255,20,0.55);
  animation: tm-pulse 2s infinite;
}
@keyframes tm-pulse {
  0% { box-shadow: 0 0 0 0 rgba(57,255,20,0.5); }
  70% { box-shadow: 0 0 0 8px rgba(57,255,20,0); }
  100% { box-shadow: 0 0 0 0 rgba(57,255,20,0); }
}

.tm-countrybar {
  display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center;
  margin: 0 0 1rem;
}
.tm-pill {
  display: inline-flex; align-items: center; gap: 0.35rem;
  padding: 0.36rem 0.72rem;
  border-radius: 999px;
  background: rgba(255,255,255,0.035);
  border: 1px solid var(--tm-border);
  color: #C9D4DF;
  font-size: 0.76rem;
  font-weight: 600;
}
.tm-pill.accent { color: var(--tm-orange); border-color: rgba(255,107,53,0.32); }

.tm-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.75rem;
  margin: 0 0 1.05rem;
}
.tm-stat {
  padding: 0.85rem 0.95rem;
  border-radius: 15px;
  border: 1px solid var(--tm-border);
  background: linear-gradient(180deg, rgba(255,255,255,0.035), rgba(255,255,255,0.012));
}
.tm-stat .value { font-size: 1.3rem; font-weight: 900; color: #FFFFFF; letter-spacing: -0.03em; }
.tm-stat .value.orange { color: var(--tm-orange); }
.tm-stat .value.green { color: var(--tm-green); }
.tm-stat .label { font-size: 0.67rem; color: var(--tm-muted); text-transform: uppercase; letter-spacing: 0.1em; margin-top: 0.12rem; }

.tm-section-title {
  display: flex; align-items: baseline; justify-content: space-between;
  gap: 1rem; margin: 1.35rem 0 0.7rem;
}
.tm-section-title h2 {
  color: #FFFFFF; font-size: 1.18rem; font-weight: 850; letter-spacing: -0.02em; margin: 0;
}
.tm-section-title span { color: var(--tm-muted); font-size: 0.78rem; }

.tm-card {
  display: flex;
  gap: 0.95rem;
  padding: 0.95rem 1rem;
  margin-bottom: 0.62rem;
  border: 1px solid var(--tm-border);
  border-radius: 17px;
  background: linear-gradient(180deg, rgba(255,255,255,0.032), rgba(255,255,255,0.010));
  transition: border-color 0.15s ease, transform 0.15s ease, background 0.15s ease;
}
.tm-card:hover {
  border-color: rgba(255,107,53,0.34);
  transform: translateY(-1px);
  background: linear-gradient(180deg, rgba(255,107,53,0.055), rgba(255,255,255,0.012));
}
.tm-rank {
  flex: 0 0 46px;
  height: 46px;
  display: grid; place-items: center;
  border-radius: 13px;
  background: #1a232d;
  border: 1px solid var(--tm-border);
  font-weight: 900;
  font-size: 0.92rem;
  color: #C7D2DD;
}
.tm-rank.top {
  background: linear-gradient(135deg, var(--tm-orange), #ff9a6f);
  color: #150a06;
  border-color: transparent;
}
.tm-card-body { flex: 1 1 auto; min-width: 0; }
.tm-card-head {
  display: flex; justify-content: space-between; gap: 1rem; align-items: flex-start;
}
.tm-topic {
  color: #FFFFFF; font-weight: 800; font-size: 1.04rem; line-height: 1.25;
  overflow-wrap: anywhere;
}
.tm-scorebox { text-align: right; flex: 0 0 auto; }
.tm-score { color: #FFFFFF; font-weight: 900; font-size: 1.35rem; line-height: 1; letter-spacing: -0.04em; }
.tm-score small { color: var(--tm-muted); font-size: 0.65rem; font-weight: 600; }
.tm-badge {
  display: inline-block; margin-top: 0.3rem; padding: 0.2rem 0.52rem;
  border-radius: 999px; font-size: 0.67rem; font-weight: 800; white-space: nowrap;
}
.tm-badge.high { color: #1a0a04; background: var(--tm-orange); }
.tm-badge.good { color: #201704; background: var(--tm-good); }
.tm-badge.watch { color: #041c27; background: var(--tm-watch); }
.tm-badge.low { color: #e8edf2; background: #3a4652; }

.tm-chips { display: flex; flex-wrap: wrap; gap: 0.3rem; margin-top: 0.45rem; }
.tm-chip {
  font-size: 0.62rem; font-weight: 800; letter-spacing: 0.06em;
  padding: 0.16rem 0.45rem; border-radius: 6px;
  border: 1px solid rgba(255,255,255,0.09);
  color: #AEBBC7; background: rgba(255,255,255,0.03);
}
.tm-chip.hot { color: var(--tm-orange); border-color: rgba(255,107,53,0.35); background: rgba(255,107,53,0.08); }
.tm-chip.yt { color: #ff5d5d; border-color: rgba(255,93,93,0.32); background: rgba(255,93,93,0.07); }
.tm-chip.week { color: var(--tm-green); border-color: rgba(57,255,20,0.28); background: rgba(57,255,20,0.06); }

.tm-bar {
  position: relative; height: 8px; margin: 0.62rem 0 0.62rem;
  background: #1b2530; border-radius: 999px; overflow: hidden;
}
.tm-bar > span {
  display: block; height: 100%; border-radius: 999px;
  background: linear-gradient(90deg, var(--tm-orange), #FFC857 55%, var(--tm-green));
  box-shadow: 0 0 14px rgba(255,107,53,0.35);
}

.tm-meta {
  display: flex; flex-wrap: wrap; gap: 0.4rem 0.9rem;
  align-items: center; color: #9DABB9; font-size: 0.75rem;
}
.tm-meta b { color: #DDE6EE; font-weight: 800; }
.tm-meta .tm-link {
  margin-left: auto; color: #170b06; font-weight: 800; text-decoration: none;
  padding: 0.3rem 0.65rem; border-radius: 8px;
  background: linear-gradient(135deg, var(--tm-orange), #FF9A6F);
  border: 1px solid rgba(255,107,53,0.55);
  font-size: 0.71rem; white-space: nowrap;
}
.tm-meta .tm-link:hover { color: #170b06; filter: brightness(1.08); }

.tm-empty {
  padding: 2.4rem 1rem; text-align: center; border: 1px dashed rgba(255,255,255,0.14);
  border-radius: 18px; color: var(--tm-muted); background: rgba(255,255,255,0.012);
}
.tm-empty strong { color: var(--tm-text); display: block; margin-bottom: 0.35rem; }

.tm-footer {
  margin-top: 2.2rem; padding-top: 1rem; border-top: 1px solid var(--tm-border);
  display: flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap;
  color: #6F7E8D; font-size: 0.75rem;
}
.tm-footer b { color: #B6C3CF; }

div[data-testid="stExpander"] {
  border: 1px solid var(--tm-border) !important;
  border-radius: 16px !important;
  background: rgba(255,255,255,0.018) !important;
  overflow: hidden;
}
div[data-testid="stExpander"] summary { color: #DCE5ED; font-weight: 800; }

.tm-method-grid {
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0.6rem;
  margin: 0.6rem 0 1rem;
}
.tm-method {
  border: 1px solid var(--tm-border); border-radius: 12px; padding: 0.7rem;
  background: rgba(255,255,255,0.02);
}
.tm-method b { color: var(--tm-orange); display: block; font-size: 1.15rem; }
.tm-method span { color: var(--tm-muted); font-size: 0.72rem; }

@media (max-width: 820px) {
  .tm-hero { flex-direction: column; align-items: flex-start; }
  .tm-datebox { text-align: left; }
  .tm-live { justify-content: flex-start; }
  .tm-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .tm-method-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .tm-card-head { flex-direction: column; gap: 0.35rem; }
  .tm-scorebox { text-align: left; }
  .tm-meta .tm-link { margin-left: 0; }
}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def render_header(country_name: str, timezone: str) -> None:
    date_label = html.escape(today_label(timezone))
    country = html.escape(country_name)
    st.markdown(
        f"""
        <div class="tm-hero">
          <div class="tm-brand">
            <div class="tm-mark">📡</div>
            <div>
              <div class="tm-eyebrow">Radar LATAM · datos en vivo</div>
              <h1>TrendManu <span>· by Manuel</span></h1>
              <p class="tm-tagline">Tu radar diario de temas virales para YouTube LATAM</p>
            </div>
          </div>
          <div class="tm-datebox">
            <div class="tm-date-label">Hoy</div>
            <div class="tm-date">{date_label}</div>
            <div class="tm-live"><span class="tm-dot"></span> {country} · Google Trends + YouTube</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_country_bar(data: DashboardData, timezone: str, analyzed: int) -> None:
    from .config import COUNTRIES

    country = COUNTRIES.get(data.country, COUNTRIES["MX"])
    updated = html.escape(format_datetime(data.fetched_at, timezone))
    st.markdown(
        f"""
        <div class="tm-countrybar">
          <span class="tm-pill accent">📍 {html.escape(country.name)}</span>
          <span class="tm-pill">🕒 Datos al {updated}</span>
          <span class="tm-pill">📊 {format_int(analyzed)} temas analizados</span>
          <span class="tm-pill">🔥 {format_int(data.daily_count)} tendencias 24 h</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stats(ranked: list[ScoredCandidate], data: DashboardData) -> None:
    high = sum(1 for item in ranked if item.score >= 80)
    rising = sum(1 for item in data.candidates if "rising" in item.signals)
    if not data.youtube_enabled:
        youtube_status = "Sin API key"
    elif any(candidate.youtube.available for candidate in data.candidates):
        youtube_status = "Activa"
    else:
        youtube_status = "Con error"
    st.markdown(
        f"""
        <div class="tm-stats">
          <div class="tm-stat">
            <div class="value">{format_int(len(data.candidates))}</div>
            <div class="label">Candidatos detectados</div>
          </div>
          <div class="tm-stat">
            <div class="value orange">{format_int(high)}</div>
            <div class="label">Alta oportunidad (80+)</div>
          </div>
          <div class="tm-stat">
            <div class="value green">{format_int(rising)}</div>
            <div class="label">Rising queries</div>
          </div>
          <div class="tm-stat">
            <div class="value">{html.escape(youtube_status)}</div>
            <div class="label">YouTube Data API</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _signal_chips(item: ScoredCandidate) -> str:
    candidate = item.candidate
    chips: list[str] = []
    if "rising" in candidate.signals:
        chips.append('<span class="tm-chip hot">RISING</span>')
    if "daily" in candidate.signals:
        chips.append('<span class="tm-chip">24 H</span>')
    if "weekly" in candidate.signals or "related_top" in candidate.signals or "rising" in candidate.signals:
        chips.append('<span class="tm-chip week">7 D</span>')
    if "youtube" in candidate.sources:
        chips.append('<span class="tm-chip yt">YOUTUBE</span>')
    return f'<div class="tm-chips">{"".join(chips)}</div>' if chips else ""


def render_cards(ranked: list[ScoredCandidate]) -> None:
    if not ranked:
        st.markdown(
            """
            <div class="tm-empty">
              <strong>No hay temas para mostrar</strong>
              Prueba quitando palabras excluidas o seleccionando más categorías.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    parts: list[str] = []
    for index, item in enumerate(ranked, start=1):
        candidate = item.candidate
        topic = html.escape(display_topic(candidate.topic))
        url = html.escape(youtube_search_url(candidate.topic), quote=True)
        rank_class = "tm-rank top" if index <= 3 else "tm-rank"
        source = html.escape(item.source_label)
        volume = html.escape(f"≈ {format_volume(item.volume)}" if item.volume else "—")
        views_label = format_volume(candidate.youtube.views_7d) if candidate.youtube.available else "—"
        views_label = html.escape(views_label)
        videos = (
            format_int(candidate.youtube.total_results)
            if candidate.youtube.available
            else "—"
        )
        score_title = html.escape(
            f"Búsqueda {item.search_score} · Tracción {item.traction_score} · "
            f"Competencia {item.competition_score} · Afinidad {item.affinity_score}"
        )

        parts.append(
            f"""
            <div class="tm-card">
              <div class="{rank_class}">#{index}</div>
              <div class="tm-card-body">
                <div class="tm-card-head">
                  <div>
                    <div class="tm-topic">{topic}</div>
                    {_signal_chips(item)}
                  </div>
                  <div class="tm-scorebox">
                    <div class="tm-score">{item.score}<small>/100</small></div>
                    <span class="tm-badge {item.label_key}">{html.escape(item.label)}</span>
                  </div>
                </div>
                <div class="tm-bar" title="{score_title}"><span style="width:{max(3, item.score)}%"></span></div>
                <div class="tm-meta">
                  <span>📌 Fuente: <b>{source}</b></span>
                  <span>🔎 Volumen est.: <b>{volume}</b></span>
                  <span>🎬 Competencia: <b>{videos} videos</b></span>
                  <span>👁️ Tracción: <b>{views_label} vistas/7d</b></span>
                  <a class="tm-link" href="{url}" target="_blank" rel="noopener noreferrer">Ver en YouTube ↗</a>
                </div>
              </div>
            </div>
            """
        )

    st.markdown("".join(parts), unsafe_allow_html=True)


def render_section_title(ranked: list[ScoredCandidate]) -> None:
    st.markdown(
        f"""
        <div class="tm-section-title">
          <h2>TOP 10 · Temas del día</h2>
          <span>{format_int(len(ranked))} temas ordenados por Score de Oportunidad Viral</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_methodology() -> None:
    with st.expander("¿Por qué estos temas? · Metodología"):
        st.markdown(
            f"""
**TrendManu no guarda historial ni preferencias.** Cada consulta se arma en vivo con
Google Trends y YouTube Data API v3 para el país elegido.

1. **Señales de Google Trends.** Leemos las tendencias de las últimas 24 horas del feed
   público de Google Trends, las *rising queries* y las búsquedas relacionadas de los
   últimos 7 días. Las rising queries reciben el mayor peso de búsqueda.
2. **Competencia y tracción en YouTube.** Para cada tema buscamos videos publicados en
   los últimos 7 días y sumamos sus vistas. Menos videos recientes y más vistas
   acumuladas significan una mejor oportunidad.
3. **Afinidad.** Comparamos el tema, sus noticias y sus tags con las categorías que
   marcaste en la barra lateral ({", ".join(CATEGORIES)}).
4. **Score final.** La combinación ponderada se redondea a un entero de 0 a 100.

<div class="tm-method-grid">
  <div class="tm-method"><b>40%</b><span>Velocidad de búsqueda en Google Trends</span></div>
  <div class="tm-method"><b>30%</b><span>Tracción: vistas de videos de 7 días</span></div>
  <div class="tm-method"><b>20%</b><span>Competencia: menos videos, mejor</span></div>
  <div class="tm-method"><b>10%</b><span>Afinidad con tus categorías</span></div>
</div>

**Etiquetas:** 80–100 🔥 Alta oportunidad · 60–79 ⚡ Buena oportunidad ·
40–59 👀 Vigilar · 0–39 ❄️ Baja prioridad.

**Nota sobre los datos.** Google Trends no publica volúmenes absolutos de búsqueda:
el «volumen est.» se estima con el tráfico aproximado del feed y el crecimiento de
cada query. En YouTube, las vistas corresponden a videos publicados en los últimos
7 días; la API no entrega vistas por rango de fechas. TrendManu exige
`YOUTUBE_API_KEY` para arrancar. Si YouTube no responde o la cuota se agota, las
métricas faltantes usan un valor neutral de 50/100 y el score sigue siendo una
señal relativa válida.
            """,
            unsafe_allow_html=True,
        )


def render_footer() -> None:
    st.markdown(
        """
        <div class="tm-footer">
          <span><b>TrendManu</b> © 2026 · Hecho para creadores de LATAM</span>
          <span>Datos frescos por ejecución · Sin historial · Sin persistencia</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
