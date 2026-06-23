from utils.request_helper import RequestHelper


class TransactionAPI:
    def __init__(self, client: RequestHelper):
        self.client = client

    def get_transactions(self, account_id: str, limit: int | None = None):
        params = {"limit": limit} if limit else None
        return self.client.get(f"/accounts/{account_id}/transactions", params=params)

    def get_transaction_details(self, transaction_id: str):
        return self.client.get(f"/transactions/{transaction_id}")

    def get_recent_transactions(self, account_id: str):
        return self.client.get(f"/accounts/{account_id}/transactions/recent")
