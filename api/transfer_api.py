from utils.request_helper import RequestHelper


class TransferAPI:
    def __init__(self, client: RequestHelper):
        self.client = client

    def transfer_funds(self, payload: dict):
        return self.client.post("/transfers", json=payload)
