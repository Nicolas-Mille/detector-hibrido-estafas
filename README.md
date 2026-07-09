# Detector Híbrido de Estafas

![CI](https://github.com/Nicolas-Mille/detector-hibrido-estafas/actions/workflows/ci.yml/badge.svg)

Detector automatizado de estafas en publicaciones de venta de marketplaces P2P (MercadoLibre, Facebook Marketplace). El usuario ingresa la URL de una publicación y el sistema devuelve un score de riesgo (0–100) con el desglose de alertas que lo justifican.

## Arquitectura

El corazón del proyecto es un pipeline en cascada diseñado para minimizar el costo de IA en producción: cada nivel resuelve lo que puede y solo escala al siguiente cuando hay riesgo.

```
URL → Caché SQL (TTL 7 días) → Scraper → Nivel 0: heurísticas → Nivel 1: ML local → Nivel 2: IA multimodal
        └─ hit: respuesta $0      └─ red flag: salto directo al Nivel 2   └─ riesgo bajo: luz verde $0
```

| Nivel | Técnica | Costo |
|---|---|---|
| Caché | MySQL, clave = hash de URL normalizada | $0 |
| 0 — Heurísticas | Reglas declarativas (precio, antigüedad de cuenta, keywords de urgencia) | $0 |
| 1 — ML local | Random Forest calibrado (scikit-learn) sobre features del vendedor | $0 |
| 2 — IA multimodal | Claude analiza imagen + texto como perito forense, con salida JSON estricta | pago por análisis |

## Estado actual

**Fase 0 — esqueleto del proyecto.** Backend FastAPI con `GET /health`, modelo `ListingSnapshot` con migración Alembic, frontend React + Vite + TypeScript, MySQL en Docker y CI con lint + tests.

**Fase 1 — ingesta.** `POST /api/ingest` recibe una URL de publicación, detecta la plataforma, extrae los datos básicos y los guarda como `ListingSnapshot` normalizado en MySQL. Todavía **no hay** detección de fraude: ni heurísticas, ni comparación de precio de mercado, ni ML, ni Claude API, ni análisis de imagen. Eso llega en las fases siguientes.

### Cómo probar POST /api/ingest

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"url": "https://articulo.mercadolibre.com.ar/MLA-123456-iphone-15-_JM"}'
```

Respuesta de ejemplo:

```json
{
  "status": "success",
  "platform": "mercadolibre",
  "source": "live_scrape",
  "snapshot": {
    "id": "5f3a...",
    "title": "iPhone 15 128GB",
    "price": 850000,
    "currency": "ARS",
    "image_url": "https://http2.mlstatic.com/...",
    "normalized_url": "https://articulo.mercadolibre.com.ar/MLA-123456-iphone-15-_JM"
  },
  "warnings": []
}
```

Con una URL no soportada:

```json
{ "status": "error", "platform": "unsupported", "message": "URL platform is not supported yet" }
```

### Adaptadores

- **`MercadoLibreAdapter`**: scraping liviano con `httpx` + `BeautifulSoup` (sin Playwright). Prioriza JSON-LD (`application/ld+json`), después OpenGraph, después selectores HTML básicos como último recurso. Si MercadoLibre no entrega algún dato (por ejemplo, la reputación del vendedor), el campo queda en `null` y se agrega un `warning`; la respuesta sigue siendo válida.
- **`FacebookFixtureAdapter`**: Facebook Marketplace real queda **fuera de esta fase** por restricciones técnicas (login, fragilidad del scraping, posibles violaciones de los términos de uso). Este adaptador resuelve URLs demo/reconocidas contra fixtures JSON en `backend/app/fixtures/facebook/`, para validar la arquitectura de adaptadores sin scraping real.

### `id` de un snapshot

El `id` que devuelve `ListingSnapshotRead` es el hash SHA-256 de la URL normalizada (`url_hash`), la misma clave primaria pensada desde la Fase 0 para la caché de 7 días. `POST /api/ingest` hace *upsert*: reingestar la misma publicación actualiza la fila existente en vez de crear una nueva.

### Limitaciones actuales

- No hay ningún cálculo de riesgo de estafa todavía.
- La extracción de MercadoLibre depende de selectores públicos que MercadoLibre puede cambiar sin aviso; los campos no encontrados quedan `null` con un warning, nunca rompen la request.
- Facebook Marketplace usa fixtures fijos, no hay scraping real.
- No hay caché con TTL activo todavía (el upsert existe, pero la lógica de "hit de caché sin re-scrapear" es de una fase posterior).

## Levantar el entorno

Requiere Docker.

```bash
cp .env.example .env
docker compose up --build
# aplicar la migración inicial
docker compose exec api alembic upgrade head
```

- Frontend: http://localhost:5173
- API: http://localhost:8000 (docs en http://localhost:8000/docs)

## Desarrollo local sin Docker

```bash
# Backend
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload

# Tests y lint
pytest
ruff check .

# Frontend
cd frontend
npm install
npm run dev
```

## Roadmap

- [x] Fase 0 — esqueleto: API, DB, frontend, Docker, CI
- [x] Fase 1 — ingesta: `POST /api/ingest`, adaptador MercadoLibre (httpx + BeautifulSoup), Facebook Marketplace por fixtures
- [ ] Fase 2 — heurísticas + precio mediano de mercado
- [ ] Fase 3 — modelo ML local con dataset documentado y métricas
- [ ] Fase 4 — integración Claude multimodal (structured outputs + prompt caching)
- [ ] Fase 5 — orquestador del pipeline + API asíncrona
- [ ] Fase 6 — dashboard con score y panel de transparencia del pipeline
- [ ] Fase 7 — deploy en VPS + demo

## Consideraciones éticas y legales

El scraping de Facebook Marketplace viola sus términos de servicio, por lo que ese adaptador funciona solo en modo demo contra fixtures HTML guardados. La fuente principal de datos es la API pública oficial de MercadoLibre. Este proyecto tiene fines educativos y de portfolio: asistir a compradores a detectar publicaciones riesgosas, no automatizar decisiones sobre terceros.
