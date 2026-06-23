import json
from pathlib import Path
from typing import Any

import allure
import requests
from jsonschema import validate
from requests import Response

from utils.config_reader import get_base_url, get_timeout
from utils.logger import get_logger


class RequestHelper:
    """Thin reusable HTTP wrapper with logging, Allure attachments, and schema validation."""

    def __init__(self, base_url: str | None = None, token: str | None = None):
        self.base_url = (base_url or get_base_url()).rstrip("/")
        self.timeout = get_timeout()
        self.session = requests.Session()
        self.logger = get_logger(self.__class__.__name__)
        if token:
            self.set_token(token)

    def set_token(self, token: str) -> None:
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def clear_token(self) -> None:
        self.session.headers.pop("Authorization", None)

    def get(self, endpoint: str, **kwargs) -> Response:
        return self._request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs) -> Response:
        return self._request("POST", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> Response:
        return self._request("DELETE", endpoint, **kwargs)

    def _request(self, method: str, endpoint: str, **kwargs) -> Response:
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault("timeout", self.timeout)
        self.logger.info("%s %s", method, url)
        if kwargs.get("json") is not None:
            self.logger.info("Request payload: %s", kwargs["json"])
            allure.attach(json.dumps(kwargs["json"], indent=2), "request_payload", allure.attachment_type.JSON)

        response = self.session.request(method=method, url=url, **kwargs)
        self.logger.info("Response status: %s", response.status_code)
        self.logger.info("Response body: %s", response.text)
        allure.attach(response.text, "response_body", allure.attachment_type.JSON)
        if response.status_code >= 400:
            self._dump_failure_response(method, endpoint, response)
        return response

    def _dump_failure_response(self, method: str, endpoint: str, response: Response) -> None:
        dump_dir = Path("reports") / "response_dumps"
        dump_dir.mkdir(parents=True, exist_ok=True)
        safe_endpoint = endpoint.strip("/").replace("/", "_") or "root"
        dump_file = dump_dir / f"{method.lower()}_{safe_endpoint}_{response.status_code}.json"
        dump_file.write_text(response.text, encoding="utf-8")
        allure.attach.file(str(dump_file), name="failure_response_dump", attachment_type=allure.attachment_type.JSON)

    @staticmethod
    def json(response: Response) -> dict[str, Any]:
        return response.json()

    @staticmethod
    def assert_status_code(response: Response, expected_status: int) -> None:
        assert response.status_code == expected_status, (
            f"Expected status {expected_status}, got {response.status_code}. Body: {response.text}"
        )

    @staticmethod
    def assert_schema(response: Response, schema_path: str | Path) -> None:
        schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
        validate(instance=response.json(), schema=schema)
