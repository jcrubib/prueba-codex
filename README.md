# Pixartprinting Price Scraper API

API en FastAPI para descubrir las llamadas internas de configuración/precio de productos de Pixartprinting y devolver precios por artículo y configuración.

## Llamadas internas detectadas (producto ejemplo)
Para `https://www.pixartprinting.es/formato-grande/impresion-lonas-microperforados/lona-frontlit/` se detectaron estas llamadas AJAX clave:

- `POST https://www.pixartprinting.es/product/validate-selection/` (devuelve configuración válida y opciones disponibles)
- `POST https://www.pixartprinting.es/product/quote/` (cotización principal)
- `POST https://www.pixartprinting.es/product/service-quote/` (servicios adicionales)

## Ejecutar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Endpoints de la API

- `POST /products` añade un nuevo producto (nombre + URL)
- `GET /products` lista productos registrados
- `POST /scrape/{product_id}` analiza el producto, descubre llamadas internas y devuelve configuración + precios

## Ejemplo

```bash
curl -X POST http://127.0.0.1:8000/products \
  -H 'content-type: application/json' \
  -d '{"name":"Lona frontlit","url":"https://www.pixartprinting.es/formato-grande/impresion-lonas-microperforados/lona-frontlit/"}'

curl -X POST http://127.0.0.1:8000/scrape/1 \
  -H 'content-type: application/json' \
  -d '{"quantities":["1","5"],"override_mcp_attributes":{"Finished Width":120,"Finished Height":100}}'
```
