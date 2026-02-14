from app.scraper import extract_prices


def test_extract_prices_collects_nested_price_nodes() -> None:
    payload = {
        "quote": [
            {"quantity": 1, "unitPrice": 12.3, "currency": "EUR"},
            {"quantity": 10, "totalPrice": 89.0, "currency": "EUR"},
        ],
        "meta": {"foo": "bar"},
    }

    result = extract_prices(payload)

    assert any("unitPrice" in entry["data"] for entry in result)
    assert any("totalPrice" in entry["data"] for entry in result)
