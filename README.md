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

**Fase 0 — esqueleto del proyecto.** Backend FastAPI con `GET /health`, modelo `ListingSnapshot` con migración Alembic, frontend React + Vite + TypeScript, MySQL en Docker y CI con lint + tests. Todavía no hay scraping, ML ni integración con la API de Claude.

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
- [ ] Fase 1 — ingesta: adaptador API MercadoLibre + Playwright (Facebook, best-effort)
- [ ] Fase 2 — heurísticas + precio mediano de mercado
- [ ] Fase 3 — modelo ML local con dataset documentado y métricas
- [ ] Fase 4 — integración Claude multimodal (structured outputs + prompt caching)
- [ ] Fase 5 — orquestador del pipeline + API asíncrona
- [ ] Fase 6 — dashboard con score y panel de transparencia del pipeline
- [ ] Fase 7 — deploy en VPS + demo

## Consideraciones éticas y legales

El scraping de Facebook Marketplace viola sus términos de servicio, por lo que ese adaptador funciona solo en modo demo contra fixtures HTML guardados. La fuente principal de datos es la API pública oficial de MercadoLibre. Este proyecto tiene fines educativos y de portfolio: asistir a compradores a detectar publicaciones riesgosas, no automatizar decisiones sobre terceros.
