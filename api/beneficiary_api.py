from utils.request_helper import RequestHelper


class BeneficiaryAPI:
    def __init__(self, client: RequestHelper):
        self.client = client

    def add_beneficiary(self, payload: dict):
        return self.client.post("/beneficiaries", json=payload)

    def list_beneficiaries(self):
        return self.client.get("/beneficiaries")

    def delete_beneficiary(self, beneficiary_id: str):
        return self.client.delete(f"/beneficiaries/{beneficiary_id}")
