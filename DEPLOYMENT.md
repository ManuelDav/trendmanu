# 🚀 Guía de despliegue de TrendManu

Esta guía cubre el despliegue local y el despliegue en **Streamlit Community
Cloud**. La regla principal es simple: **la API key de YouTube nunca se escribe en
el código ni se sube a GitHub**.

---

## 1. Requisitos previos

- Cuenta de GitHub.
- Cuenta gratuita en [Streamlit Community Cloud](https://share.streamlit.io/).
- Proyecto de Google Cloud con **YouTube Data API v3** habilitada.
- Una **API key** restringida a YouTube Data API v3.

Consulta el README para crear la API key.

---

## 2. Preparar el repositorio

Desde la carpeta del proyecto:

```bash
cd trendmanu

git init
git add .
git commit -m "feat: TrendManu dashboard"
```

Antes de subir, confirma que el archivo real de secretos está ignorado:

```bash
git check-ignore -v .streamlit/secrets.toml
```

Debe mostrar una línea indicando que `.gitignore` lo excluye. Si el archivo no
existe todavía, crea uno de prueba solo para verificar (no lo agregues al repo):

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
git status --short
```

`.streamlit/secrets.toml` **no debe aparecer** en `git status`. El ejemplo
`.streamlit/secrets.toml.example` sí puede estar en el repositorio.

Verifica que no haya claves escritas por accidente:

```bash
grep -R "AIza" . --exclude-dir=.git --exclude-dir=.venv
```

El único resultado permitido sería un texto de ejemplo/documentación, nunca una
clave real.

Sube el repositorio:

```bash
git branch -M main
git remote add origin https://github.com/TU_USUARIO/trendmanu.git
git push -u origin main
```

---

## 3. Despliegue en Streamlit Community Cloud

1. Entra a [share.streamlit.io](https://share.streamlit.io/) con tu cuenta de GitHub.
2. Pulsa **Create app** / **New app**.
3. Elige:
   - **Repository:** `TU_USUARIO/trendmanu`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Abre **Advanced settings** y selecciona **Python 3.11** o superior.
5. En **Secrets**, pega exactamente:

```toml
YOUTUBE_API_KEY = "AIza..."
```

   Reemplaza `AIza...` por tu clave real. No agregues comas al final.
6. Pulsa **Deploy**.
7. Espera a que termine la instalación de dependencias.
8. Abre la URL pública de la app y comprueba que carga el TOP 10.

> La app lee la clave con `st.secrets["YOUTUBE_API_KEY"]` al inicio de `app.py`.
> Si el secreto falta o está vacío, muestra el error
> «⚠️ Falta configurar YOUTUBE_API_KEY» y se detiene.

### Si cambias el secreto

En **App settings → Secrets**, actualiza el valor y pulsa **Reboot app**. Los
secretos no se recargan solos en todos los casos.

### Logs y diagnóstico

- **Manage app → Logs** muestra errores de instalación, imports y llamadas a APIs.
- Si aparece `KeyError: 'YOUTUBE_API_KEY'`, el secreto no está configurado o tiene
  otro nombre.
- Si aparece `API key not valid`, revisa que copiaste la clave completa y que
  YouTube Data API v3 está habilitada en Google Cloud.
- Si aparece `quotaExceeded`, se agotó la cuota diaria de YouTube Data API v3.

---

## 4. Despliegue local (para desarrollo)

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edita .streamlit/secrets.toml con tu clave real

streamlit run app.py
```

Abre `http://localhost:8501`.

No uses variables de entorno para la clave en el código: la aplicación está
diseñada para leerla desde `st.secrets`, que en local toma el archivo
`.streamlit/secrets.toml`.

---

## 5. Actualizaciones

1. Haz cambios en local.
2. Ejecuta las pruebas:

```bash
pytest -q
```

3. Haz commit y push a `main`.
4. Streamlit Community Cloud redepliega automáticamente al detectar el push.
5. Si el cambio toca secretos o dependencias, usa **Reboot app** desde el panel.

---

## 6. Checklist de seguridad antes de publicar

- [ ] `.streamlit/secrets.toml` está en `.gitignore`.
- [ ] `git status` no muestra secretos.
- [ ] `grep -R "AIza"` no encuentra claves reales en el repo.
- [ ] La API key está restringida a **YouTube Data API v3**.
- [ ] La API key no está en capturas, issues, commits ni documentación.
- [ ] Si la clave se expuso, fue revocada y reemplazada.
- [ ] El panel de Secrets de Streamlit Cloud tiene el nombre exacto
      `YOUTUBE_API_KEY`.

---

## 7. Alternativas de despliegue

TrendManu es una app estándar de Streamlit. En otros proveedores (Render,
Railway, un VPS, Docker, etc.):

- Usa el comando de arranque:

```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

- Crea `.streamlit/secrets.toml` en el servidor con la clave, fuera del control de
  versiones, o monta el archivo como secreto del proveedor.
- Define las variables de puerto que exija la plataforma.
- Asegura que el archivo de secretos tenga permisos restringidos:

```bash
chmod 600 .streamlit/secrets.toml
```

---

## 8. Problemas frecuentes en despliegue

| Síntoma | Causa probable | Solución |
|---|---|---|
| La app muestra «Falta configurar YOUTUBE_API_KEY» | Secreto ausente, mal escrito o vacío | Revisa App settings → Secrets y reinicia |
| `ModuleNotFoundError` | Falta una dependencia en `requirements.txt` | Agrégala y vuelve a desplegar |
| La app tarda en cargar | Consultas a Google Trends/YouTube en curso | Es normal; el primer render puede tardar varios segundos |
| YouTube 403 / cuota | Límite diario de 10.000 unidades | Espera el reinicio diario o usa otra clave |
| YouTube 400 / API key inválida | Clave incorrecta o API deshabilitada | Revisa Google Cloud Console |
| No aparecen temas | Filtros excluyentes o país sin tendencias | Limpia palabras excluidas y pulsa actualizar |

---

Con esto, TrendManu queda desplegado y funcionando sin exponer la API key.
