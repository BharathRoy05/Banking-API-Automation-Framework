from requests import Response


def assert_error_message(response: Response, expected_text: str) -> None:
    body = response.json()
    assert "error" in body, f"Expected error response, got: {body}"
    assert expected_text.lower() in body["error"].lower()


def assert_money_is_non_negative(value: float) -> None:
    assert isinstance(value, (int, float))
    assert value >= 0


def assert_collection_not_empty(items: list, label: str) -> None:
    assert isinstance(items, list), f"{label} should be a list"
    assert items, f"{label} should not be empty"
