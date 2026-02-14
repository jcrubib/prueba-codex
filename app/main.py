from fastapi import FastAPI, HTTPException

from app.models import Product, ProductCreate, ScrapeRequest, ScrapeResponse
from app.scraper import PixartScraper
from app.store import ProductStore

app = FastAPI(title="Pixartprinting Scraper API")
store = ProductStore()
scraper = PixartScraper()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/products", response_model=Product)
def create_product(payload: ProductCreate) -> Product:
    return store.add(payload)


@app.get("/products", response_model=list[Product])
def list_products() -> list[Product]:
    return store.list()


@app.post("/scrape/{product_id}", response_model=ScrapeResponse)
async def scrape_product(product_id: int, payload: ScrapeRequest) -> ScrapeResponse:
    product = store.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    data = await scraper.scrape(
        url=str(product.url),
        quantities=payload.quantities,
        overrides=payload.override_mcp_attributes,
    )

    return ScrapeResponse(
        product_id=product.id,
        product_url=product.url,
        discovered_endpoints=data["discovered_endpoints"],
        request_payloads=data["request_payloads"],
        configuration=data["configuration"],
        quote_response=data["quote_response"],
        service_quote_response=data["service_quote_response"],
        prices=data["prices"],
    )
