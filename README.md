# Pixartprinting Price Scraper API

API en FastAPI para descubrir llamadas internas de configuración/precio en Pixartprinting y devolver precios por artículo + configuración.

## Llamadas internas detectadas (producto ejemplo)
Para `https://www.pixartprinting.es/formato-grande/impresion-lonas-microperforados/lona-frontlit/`:

- `POST https://www.pixartprinting.es/product/validate-selection/`
- `POST https://www.pixartprinting.es/product/quote/`
- `POST https://www.pixartprinting.es/product/service-quote/`

## Ejecutar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Enlace local de ejecución:
- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`

## Endpoints

- `POST /products` añade un producto (nombre + URL)
- `GET /products` lista productos
- `POST /scrape/{product_id}` scrappea el producto y devuelve:
  - endpoints detectados,
  - payloads capturados,
  - configuración validada,
  - respuesta de quote/service-quote,
  - precios extraídos.

## Ejemplo rápido

```bash
curl -X POST http://127.0.0.1:8000/products \
  -H 'content-type: application/json' \
  -d '{"name":"Lona frontlit","url":"https://www.pixartprinting.es/formato-grande/impresion-lonas-microperforados/lona-frontlit/"}'

curl -X POST http://127.0.0.1:8000/scrape/1 \
  -H 'content-type: application/json' \
  -d '{"quantities":["1","5"],"override_mcp_attributes":{"Finished Width":120,"Finished Height":100}}'
```
