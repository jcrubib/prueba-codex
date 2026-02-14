import asyncio
import json
from typing import Any

TARGET_PATHS = {
    "validate_selection": "/product/validate-selection/",
    "quote": "/product/quote/",
    "service_quote": "/product/service-quote/",
}


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


class PixartScraper:
    async def scrape(self, url: str, quantities: list[str] | None, overrides: dict[str, Any] | None) -> dict[str, Any]:
        captured_requests: dict[str, dict | list | None] = {k: None for k in TARGET_PATHS}
        captured_responses: dict[str, dict | list | None] = {k: None for k in TARGET_PATHS}
        discovered_endpoints: set[str] = set()

        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            def handle_request(request):
                for key, path in TARGET_PATHS.items():
                    if path in request.url and captured_requests[key] is None:
                        try:
                            captured_requests[key] = request.post_data_json
                        except Exception:
                            captured_requests[key] = {"raw": request.post_data}

            async def handle_response(response):
                for key, path in TARGET_PATHS.items():
                    if path in response.url:
                        discovered_endpoints.add(response.url)
                        if captured_responses[key] is None:
                            try:
                                captured_responses[key] = await response.json()
                            except Exception:
                                captured_responses[key] = {"raw": await response.text()}

            page.on("request", handle_request)
            page.on("response", lambda resp: asyncio.create_task(handle_response(resp)))

            await page.goto(url, wait_until="domcontentloaded", timeout=120000)
            await page.wait_for_timeout(12000)

            quote_request = captured_requests.get("quote")
            service_request = captured_requests.get("service_quote")

            if isinstance(quote_request, dict):
                quote_payload = dict(quote_request)
                if quantities:
                    quote_payload["quantities"] = quantities
                if overrides:
                    quote_payload.setdefault("mcpAttributes", {}).update(overrides)
                quote_resp = await page.request.post(
                    "https://www.pixartprinting.es/product/quote/",
                    data=quote_payload,
                )
                captured_responses["quote"] = await quote_resp.json()

            if isinstance(service_request, dict):
                service_payload = dict(service_request)
                if quantities:
                    service_payload["quantities"] = quantities
                if overrides:
                    service_payload.setdefault("mcpAttributes", {}).update(overrides)
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
