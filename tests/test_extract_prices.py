from app.scraper import apply_overrides, extract_prices


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


def test_apply_overrides_sets_quantities_and_mcp_attributes() -> None:
    base = {"mcpAttributes": {"Finished Width": 100}, "quantities": ["1"]}

    updated = apply_overrides(base, ["2", "5"], {"Finished Height": 120})

    assert updated["quantities"] == ["2", "5"]
    assert updated["mcpAttributes"]["Finished Width"] == 100
    assert updated["mcpAttributes"]["Finished Height"] == 120
    assert base["quantities"] == ["1"]
