from utils.request_helper import RequestHelper


class AccountAPI:
    def __init__(self, client: RequestHelper):
        self.client = client

    def get_account(self, account_id: str):
        return self.client.get(f"/accounts/{account_id}")

    def get_balance(self, account_id: str):
        return self.client.get(f"/accounts/{account_id}/balance")

    def get_accounts(self):
        return self.client.get("/accounts")
