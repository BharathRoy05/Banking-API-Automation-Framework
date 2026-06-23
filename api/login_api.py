from utils.request_helper import RequestHelper


class LoginAPI:
    def __init__(self, client: RequestHelper):
        self.client = client

    def login(self, username: str | None, password: str | None):
        return self.client.post("/auth/login", json={"username": username, "password": password})

    def validate_token(self, token: str | None = None):
        headers = {"Authorization": f"Bearer {token}"} if token else None
        return self.client.get("/auth/validate", headers=headers)
