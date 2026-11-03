# 📡 TrendManu

**Tu radar diario de temas virales para YouTube LATAM**  
por Manuel · © 2026

TrendManu es un dashboard en Streamlit que, cada vez que lo abres o lo actualizas,
consulta Google Trends y YouTube Data API v3 para mostrar el **TOP 10 de temas del
día** con mayor probabilidad de volverse virales en México, Argentina, Colombia o
Chile.

No usa base de datos, no guarda historial y no persiste preferencias: cada consulta
se arma en vivo y se muestra en pantalla.

---

## ✨ Qué hace

1. **Google Trends**
   - Tendencias de las últimas 24 horas (feed público de Trends).
   - Rising queries y búsquedas relacionadas de los últimos 7 días.
   - Impulso semanal de los temas principales.
2. **YouTube Data API v3**
   - Cantidad de videos recientes sobre cada tema (competencia).
   - Vistas acumuladas por esos videos en los últimos 7 días (tracción).
   - Tags y hashtags de los videos más populares del país (temas propios de YouTube).
3. **Score de Oportunidad Viral (0–100)**
   - 40 % velocidad de búsqueda en Google Trends.
   - 30 % tracción en YouTube.
   - 20 % competencia (menos videos = mejor).
   - 10 % afinidad con las categorías seleccionadas.
4. **Vista final**
   - TOP 10 con posición, score, barra visual, etiqueta, fuente, volumen estimado,
     competencia, tracción y botón **Ver en YouTube**.
   - Sección colapsable **¿Por qué estos temas?** con la metodología.

---

## 🗂️ Estructura

```
trendmanu/
├── app.py                     # Punto de entrada de Streamlit
├── requirements.txt
├── requirements-dev.txt
├── README.md
├── DEPLOYMENT.md              # Guía de despliegue paso a paso
├── .streamlit/
│   ├── config.toml            # Tema oscuro y configuración del servidor
│   └── secrets.toml.example   # Plantilla de secretos (sin clave real)
├── trendmanu/
│   ├── __init__.py
│   ├── config.py              # Países, categorías, pesos y parámetros
│   ├── models.py              # Dataclasses del pipeline
│   ├── trends.py              # Google Trends (RSS + pytrends-modern)
│   ├── youtube.py             # YouTube Data API v3
│   ├── scoring.py             # Fórmula del Score de Oportunidad Viral
│   ├── pipeline.py            # Recolección, fusión y enriquecimiento
│   ├── ui.py                  # CSS y componentes visuales
│   └── utils.py               # Texto, fechas y formato
└── tests/
    ├── test_pipeline.py
    ├── test_scoring.py
    ├── test_trends.py
    ├── test_utils.py
    └── test_youtube.py
```

---

## 🚀 Instalación y ejecución local

Requiere **Python 3.11 o superior**.

```bash
cd trendmanu

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edita .streamlit/secrets.toml y coloca tu API key real

streamlit run app.py
```

La app queda disponible en `http://localhost:8501`.

### Configurar la API key de YouTube

1. Entra a [Google Cloud Console](https://console.cloud.google.com/).
2. Crea un proyecto (o usa uno existente).
3. Habilita **YouTube Data API v3** en *APIs & Services → Library*.
4. Ve a *APIs & Services → Credentials* y crea una **API key**.
5. Restringe la clave a **YouTube Data API v3** (API restrictions).
6. Copia la clave en `.streamlit/secrets.toml`:

```toml
YOUTUBE_API_KEY = "AIza..."
```

`.streamlit/secrets.toml` está en `.gitignore` y **nunca debe subirse al
repositorio**. El archivo `.streamlit/secrets.toml.example` solo contiene un
placeholder y sí puede versionarse.

`app.py` lee el secreto al inicio:

```python
try:
    YOUTUBE_API_KEY = str(st.secrets["YOUTUBE_API_KEY"]).strip()
except (KeyError, FileNotFoundError):
    st.error("⚠️ Falta configurar YOUTUBE_API_KEY. Revisa el README para instrucciones.")
    st.stop()
```

Si la clave no existe o está vacía, la aplicación se detiene con un mensaje claro.
No hay claves escritas en el código ni en el repositorio.

### Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

---

## ☁️ Despliegue

La guía completa está en **[DEPLOYMENT.md](DEPLOYMENT.md)**. Resumen para
Streamlit Community Cloud:

1. Sube el proyecto a un repositorio de GitHub **sin** `.streamlit/secrets.toml`.
2. En [share.streamlit.io](https://share.streamlit.io/), crea una app nueva y
   selecciona el repo, la rama y `app.py`.
3. En **App settings → Secrets**, pega:

```toml
YOUTUBE_API_KEY = "AIza..."
```

4. Guarda, despliega y verifica los logs. Si cambias el secreto, reinicia la app.

---

## 🧮 Cómo se calcula el score

| Componente | Peso | Qué mide |
|---|---:|---|
| Búsqueda | 40 % | Rising queries (prioridad máxima), tendencias 24 h e impulso de 7 días |
| Tracción | 30 % | Vistas acumuladas por videos publicados en los últimos 7 días |
| Competencia | 20 % | Cantidad de videos recientes sobre el tema (menos es mejor) |
| Afinidad | 10 % | Coincidencia con las categorías marcadas en la barra lateral |

Las escalas de tracción y competencia son logarítmicas para evitar que un solo tema
con millones de vistas aplaste al resto.

**Etiquetas**

- 80–100 → 🔥 Alta oportunidad
- 60–79 → ⚡ Buena oportunidad
- 40–59 → 👀 Vigilar
- 0–39 → ❄️ Baja prioridad

### Notas honestas sobre los datos

- Google Trends **no publica volúmenes absolutos** de búsqueda. El campo
  «Volumen est.» se estima con el tráfico aproximado del feed diario y el crecimiento
  de la query. Es una referencia relativa, no una cifra de Keyword Planner.
- YouTube no expone «vistas en los últimos 7 días» por video. Sumamos las vistas
  **totales actuales** de videos **publicados** en los últimos 7 días, que es la mejor
  aproximación disponible con la API.
- El feed de Google Trends puede cambiar o limitar peticiones. TrendManu incluye
  lectura directa del RSS como respaldo y avisos visibles en pantalla.
- La cuota gratuita de YouTube Data API v3 es de 10.000 unidades/día. Cada búsqueda
  de tema consume ~100 unidades. TrendManu consulta como máximo 15 temas por carga.

---

## 🎛️ Controles

- **País:** MX, AR, CO o CL.
- **Categorías de interés:** tecnología, finanzas, motivación, entretenimiento y
  educación.
- **Palabras excluidas:** texto separado por comas; se ocultan los temas que las
  contengan.
- **🔄 Actualizar tendencias ahora:** vuelve a consultar todas las fuentes.

Cambiar filtros de categorías o palabras excluidas recalcula el score al instante sin
volver a gastar cuota de API. Cambiar de país o pulsar el botón de actualización sí
hace una consulta nueva.

---

## ⚠️ Solución de problemas

| Problema | Qué revisar |
|---|---|
| «Falta configurar YOUTUBE_API_KEY» | Crea `.streamlit/secrets.toml` desde el ejemplo y reinicia Streamlit. En producción, revisa App settings → Secrets. |
| YouTube devuelve 403 / cuota | Espera el reinicio diario de cuota, revisa las restricciones de la API key o usa otra clave. |
| YouTube devuelve 400 / API key inválida | Verifica que la clave esté bien copiada y que YouTube Data API v3 esté habilitada. |
| Google Trends no responde | Suele ser temporal o un bloqueo por rate limit; pulsa actualizar más tarde. |
| No aparecen temas | Revisa palabras excluidas, conexión a internet y que el país tenga tendencias activas. |

---

## 🔐 Seguridad

- No escribas la API key en `app.py`, tests, README ni capturas.
- No subas `.streamlit/secrets.toml` a GitHub.
- Si una clave se expone, revócala en Google Cloud Console y crea una nueva.
- Restringe la clave a YouTube Data API v3 y, si es posible, a las IPs de tu
  despliegue.

---

Hecho para creadores de LATAM. Sin historial, sin ruido: solo el radar del día.
