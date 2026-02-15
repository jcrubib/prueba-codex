import asyncio
import json
from typing import Any

TARGET_PATHS = {
    "validate_selection": "/product/validate-selection/",
    "quote": "/product/quote/",
    "service_quote": "/product/service-quote/",
}


class ScraperError(RuntimeError):
    """Raised when scraping data cannot be captured or replayed."""


def _safe_json_loads(raw: str | None) -> dict | list | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def extract_prices(payload: Any) -> list[dict]:
    prices: list[dict] = []

    def walk(node: Any, path: str = "") -> None:
        if isinstance(node, dict):
            price_like = {
                k: v
                for k, v in node.items()
                if any(token in k.lower() for token in ("price", "amount", "total", "currency"))
            }
            if price_like:
                prices.append({"path": path or "$", "data": price_like})
            for key, value in node.items():
                walk(value, f"{path}.{key}" if path else key)
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                walk(item, f"{path}[{idx}]")

    walk(payload)
    unique: list[dict] = []
    seen = set()
    for item in prices:
        serialized = json.dumps(item, sort_keys=True, default=str)
        if serialized not in seen:
            seen.add(serialized)
            unique.append(item)
    return unique


def apply_overrides(base_payload: dict[str, Any], quantities: list[str] | None, overrides: dict[str, Any] | None) -> dict[str, Any]:
    payload = json.loads(json.dumps(base_payload))
    if quantities:
        payload["quantities"] = quantities
    if overrides:
        payload.setdefault("mcpAttributes", {}).update(overrides)
    return payload


class PixartScraper:
    async def scrape(self, url: str, quantities: list[str] | None, overrides: dict[str, Any] | None) -> dict[str, Any]:
        captured_requests: dict[str, dict | list | None] = {k: None for k in TARGET_PATHS}
        captured_responses: dict[str, dict | list | None] = {k: None for k in TARGET_PATHS}
        discovered_endpoints: set[str] = set()
        events = {k: asyncio.Event() for k in TARGET_PATHS}

        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            async def handle_request(request) -> None:
                for key, path in TARGET_PATHS.items():
                    if path in request.url and captured_requests[key] is None:
                        captured_requests[key] = _safe_json_loads(request.post_data) or {"raw": request.post_data}

            async def handle_response(response) -> None:
                for key, path in TARGET_PATHS.items():
                    if path in response.url:
                        discovered_endpoints.add(response.url)
                        if captured_responses[key] is None:
                            try:
                                captured_responses[key] = await response.json()
                            except Exception:
                                captured_responses[key] = {"raw": await response.text()}
                        events[key].set()

            page.on("request", lambda req: asyncio.create_task(handle_request(req)))
            page.on("response", lambda resp: asyncio.create_task(handle_response(resp)))

            await page.goto(url, wait_until="domcontentloaded", timeout=120000)
            try:
                await asyncio.wait_for(events["quote"].wait(), timeout=25)
            except asyncio.TimeoutError as exc:
                await browser.close()
                raise ScraperError("No se detectó la llamada /product/quote/ en la página objetivo.") from exc

            quote_request = captured_requests.get("quote")
            service_request = captured_requests.get("service_quote")

            if not isinstance(quote_request, dict):
                await browser.close()
                raise ScraperError("No se pudo capturar el payload base de /product/quote/.")

            quote_payload = apply_overrides(quote_request, quantities, overrides)
            quote_resp = await page.request.post(
                "https://www.pixartprinting.es/product/quote/",
                data=quote_payload,
            )
            captured_responses["quote"] = await quote_resp.json()

            if isinstance(service_request, dict):
                service_payload = apply_overrides(service_request, quantities, overrides)
                service_resp = await page.request.post(
                    "https://www.pixartprinting.es/product/service-quote/",
                    data=service_payload,
                )
                captured_responses["service_quote"] = await service_resp.json()

            await browser.close()

        quote_payload = captured_responses.get("quote") or {}
        prices = extract_prices(quote_payload)

        return {
            "discovered_endpoints": sorted(discovered_endpoints),
            "request_payloads": captured_requests,
            "configuration": captured_responses.get("validate_selection") or {},
            "quote_response": captured_responses.get("quote") or {},
            "service_quote_response": captured_responses.get("service_quote") or {},
            "prices": prices,
        }
