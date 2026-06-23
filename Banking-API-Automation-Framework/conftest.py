from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import pytest
import requests
from werkzeug.serving import make_server

from api.account_api import AccountAPI
from api.beneficiary_api import BeneficiaryAPI
from api.login_api import LoginAPI
from api.transaction_api import TransactionAPI
from api.transfer_api import TransferAPI
from mock_api.app import create_app
from utils.config_reader import ROOT_DIR, get_base_url, should_auto_start_mock_api
from utils.request_helper import RequestHelper


class ServerThread(threading.Thread):
    def __init__(self, host: str, port: int):
        super().__init__(daemon=True)
        app = create_app()
        self.server = make_server(host, port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


@pytest.fixture(scope="session", autouse=True)
def mock_banking_api():
    if not should_auto_start_mock_api():
        yield
        return

    base_url = get_base_url()
    host = base_url.replace("http://", "").replace("https://", "").split(":")[0]
    port = int(base_url.rsplit(":", 1)[-1])
    server = ServerThread(host, port)
    server.start()
    for _ in range(30):
        try:
            requests.get(f"{base_url}/health", timeout=1)
            break
        except requests.RequestException:
            time.sleep(0.1)
    yield
    server.shutdown()


@pytest.fixture(autouse=True)
def reset_mock_state():
    requests.post(f"{get_base_url()}/test/reset", timeout=2)


@pytest.fixture(scope="session")
def users():
    with (ROOT_DIR / "test_data" / "users.json").open(encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture
def client():
    return RequestHelper()


@pytest.fixture
def login_api(client):
    return LoginAPI(client)


@pytest.fixture
def auth_token(login_api, users):
    valid_user = users["valid_user"]
    response = login_api.login(valid_user["username"], valid_user["password"])
    RequestHelper.assert_status_code(response, 200)
    return response.json()["token"]


@pytest.fixture
def auth_client(auth_token):
    return RequestHelper(token=auth_token)


@pytest.fixture
def account_api(auth_client):
    return AccountAPI(auth_client)


@pytest.fixture
def beneficiary_api(auth_client):
    return BeneficiaryAPI(auth_client)


@pytest.fixture
def transfer_api(auth_client):
    return TransferAPI(auth_client)


@pytest.fixture
def transaction_api(auth_client):
    return TransactionAPI(auth_client)


@pytest.fixture(scope="session")
def schemas_dir() -> Path:
    return ROOT_DIR / "schemas"
