from pydantic import BaseModel, HttpUrl, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1)
    url: HttpUrl


class Product(ProductCreate):
    id: int


class ScrapeRequest(BaseModel):
    quantities: list[str] | None = None
    override_mcp_attributes: dict[str, str | int | float | bool] | None = None


class ScrapeResponse(BaseModel):
    product_id: int
    product_url: HttpUrl
    discovered_endpoints: list[str]
    request_payloads: dict[str, dict | list | None]
    configuration: dict
    quote_response: dict | list
    service_quote_response: dict | list
    prices: list[dict]
