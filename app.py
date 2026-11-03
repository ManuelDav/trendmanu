"""TrendManu · Tu radar diario de temas virales para YouTube LATAM."""

from __future__ import annotations

import streamlit as st

from trendmanu.config import (
    CATEGORIES,
    COUNTRIES,
    DEFAULT_COUNTRY,
)
from trendmanu.pipeline import build_dashboard_data, rank_dashboard
from trendmanu.ui import (
    inject_css,
    render_cards,
    render_country_bar,
    render_footer,
    render_header,
    render_methodology,
    render_section_title,
    render_stats,
)
from trendmanu.utils import configure_logging, format_datetime

st.set_page_config(
    page_title="TrendManu · Radar de temas virales",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# Secreto: la API key vive en .streamlit/secrets.toml (local) o en el
# panel de Secrets de Streamlit Community Cloud (producción).
# Nunca se escribe en el código ni se sube al repositorio.
# ----------------------------------------------------------------------
try:
    YOUTUBE_API_KEY = str(st.secrets["YOUTUBE_API_KEY"]).strip()
except (KeyError, FileNotFoundError):
    st.error("⚠️ Falta configurar YOUTUBE_API_KEY. Revisa el README para instrucciones.")
    st.stop()

if not YOUTUBE_API_KEY:
    st.error("⚠️ Falta configurar YOUTUBE_API_KEY. Revisa el README para instrucciones.")
    st.stop()

configure_logging()
inject_css()


# ----------------------------------------------------------------------
# Barra lateral
# ----------------------------------------------------------------------
if "tm_nonce" not in st.session_state:
    st.session_state["tm_nonce"] = 0

with st.sidebar:
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.2rem;">
          <div style="width:38px;height:38px;border-radius:11px;display:grid;place-items:center;
                      background:linear-gradient(135deg,rgba(255,107,53,.25),rgba(57,255,20,.12));
                      border:1px solid rgba(255,107,53,.35);font-size:1.15rem;">📡</div>
          <div>
            <div style="font-weight:900;color:#fff;font-size:1.05rem;letter-spacing:-.02em;">TrendManu</div>
            <div style="color:#8A99A8;font-size:.72rem;">by Manuel · radar LATAM</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Temas con mayor probabilidad de volverse virales esta semana.")
    st.divider()

    country_code = st.selectbox(
        "País",
        options=list(COUNTRIES.keys()),
        index=list(COUNTRIES.keys()).index(DEFAULT_COUNTRY),
        format_func=lambda code: f"{COUNTRIES[code].name} ({code})",
        help="Google Trends y YouTube se consultan para este país.",
    )

    st.markdown("**Categorías de interés**")
    selected_categories: list[str] = []
    for category in CATEGORIES:
        if st.checkbox(category.capitalize(), value=True, key=f"tm_cat_{category}"):
            selected_categories.append(category)

    excluded_text = st.text_input(
        "Palabras excluidas",
        placeholder="farándula, apuestas, política...",
        help="Separa las palabras con comas. Se ocultan los temas que las contengan.",
    )

    st.write("")
    refresh_clicked = st.button("🔄 Actualizar tendencias ahora", use_container_width=True)

    st.divider()
    st.success("YOUTUBE_API_KEY cargada desde secrets", icon="✅")
    st.caption(
        "Configura la clave en `.streamlit/secrets.toml` (local) o en el panel "
        "de Secrets de Streamlit Community Cloud (producción)."
    )

# ----------------------------------------------------------------------
# Datos frescos (una vez por país / actualización, sin persistencia)
# ----------------------------------------------------------------------
if refresh_clicked:
    st.session_state["tm_nonce"] += 1
    st.session_state.pop("tm_data", None)
    st.session_state.pop("tm_data_key", None)

data = None
data_key = f"{country_code}:{st.session_state['tm_nonce']}"

if st.session_state.get("tm_data_key") != data_key or "tm_data" not in st.session_state:
    with st.spinner("Escaneando Google Trends y YouTube…"):
        try:
            data = build_dashboard_data(country_code, YOUTUBE_API_KEY)
        except Exception as exc:  # noqa: BLE001 - mostrar error amable al usuario
            st.error(
                "No se pudieron cargar las tendencias. Revisa tu conexión, la API key "
                "y vuelve a intentarlo."
            )
            st.caption(f"Detalle técnico: {exc}")
            render_footer()
            st.stop()
        st.session_state["tm_data"] = data
        st.session_state["tm_data_key"] = data_key
else:
    data = st.session_state["tm_data"]

if data is None:
    st.error("No hay datos disponibles.")
    render_footer()
    st.stop()

country = COUNTRIES.get(country_code, COUNTRIES[DEFAULT_COUNTRY])
excluded_terms = [term.strip() for term in excluded_text.split(",") if term.strip()]
ranked = rank_dashboard(
    data,
    selected_categories=selected_categories,
    excluded_terms=excluded_terms,
    limit=10,
)

# ----------------------------------------------------------------------
# Área principal
# ----------------------------------------------------------------------
render_header(country.name, country.timezone)
render_country_bar(data, country.timezone, analyzed=len(data.candidates))

for warning in dict.fromkeys(data.warnings):
    if "YOUTUBE_API_KEY" in warning:
        st.info(warning)
    else:
        st.warning(warning)

render_stats(ranked, data)
render_section_title(ranked)
render_cards(ranked)
render_methodology()
render_footer()

with st.sidebar:
    st.divider()
    st.caption(
        f"Última consulta: {format_datetime(data.fetched_at, country.timezone)} · "
        f"{len(data.candidates)} candidatos"
    )
    st.caption("Los datos no se guardan: al refrescar la página se consulta de nuevo.")
