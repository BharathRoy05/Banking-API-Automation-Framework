import allure
import pytest

from utils.assertions import assert_error_message
from utils.data_generator import transfer_payload
from utils.request_helper import RequestHelper


@allure.epic("Digital Banking")
@allure.feature("Fund Transfers")
class TestTransfer:
    @pytest.mark.smoke
    @pytest.mark.transfer
    @pytest.mark.schema
    @allure.title("Customer can complete a successful fund transfer")
    def test_successful_transfer(self, transfer_api, users, schemas_dir):
        payload = transfer_payload(from_account_id=users["valid_user"]["account_id"], amount=250.25)
        response = transfer_api.transfer_funds(payload)

        RequestHelper.assert_status_code(response, 201)
        body = response.json()
        RequestHelper.assert_schema(type("Obj", (), {"json": lambda self: body["transaction"]})(), schemas_dir / "transaction_schema.json")
        assert body["message"] == "transfer successful"
        assert body["transaction"]["amount"] == payload["amount"]

    @pytest.mark.transfer
    @allure.title("Transfer reduces available balance")
    def test_transfer_updates_balance(self, account_api, transfer_api, users):
        account_id = users["valid_user"]["account_id"]
        before = account_api.get_balance(account_id).json()["available_balance"]
        transfer_api.transfer_funds(transfer_payload(from_account_id=account_id, amount=100.0))
        after = account_api.get_balance(account_id).json()["available_balance"]

        assert round(before - after, 2) == 100.0

    @pytest.mark.transfer
    @allure.title("Transfer creates a debit transaction")
    def test_transfer_creates_transaction(self, transfer_api, transaction_api, users):
        account_id = users["valid_user"]["account_id"]
        transfer_api.transfer_funds(transfer_payload(from_account_id=account_id, amount=55.0))
        history = transaction_api.get_transactions(account_id).json()["transactions"]

        assert history[0]["type"] == "DEBIT"
        assert history[0]["amount"] == 55.0

    @pytest.mark.negative
    @pytest.mark.transfer
    @allure.title("Insufficient balance is rejected")
    def test_insufficient_balance_validation(self, transfer_api, users):
        response = transfer_api.transfer_funds(
            transfer_payload(from_account_id=users["valid_user"]["account_id"], amount=999999.99)
        )

        RequestHelper.assert_status_code(response, 422)
        assert_error_message(response, "insufficient balance")

    @pytest.mark.negative
    @pytest.mark.transfer
    @pytest.mark.parametrize("amount", [0, -1, -100.50])
    @allure.title("Invalid transfer amounts are rejected")
    def test_invalid_amount_validation(self, transfer_api, users, amount):
        response = transfer_api.transfer_funds(transfer_payload(from_account_id=users["valid_user"]["account_id"], amount=amount))

        RequestHelper.assert_status_code(response, 400)
        assert_error_message(response, "greater than zero")

    @pytest.mark.negative
    @pytest.mark.transfer
    @allure.title("Invalid source account is rejected")
    def test_invalid_account_validation(self, transfer_api):
        response = transfer_api.transfer_funds(transfer_payload(from_account_id="ACC-NOT-REAL", amount=10))

        RequestHelper.assert_status_code(response, 404)
        assert_error_message(response, "source account not found")

    @pytest.mark.negative
    @pytest.mark.transfer
    @allure.title("Unknown beneficiary account is rejected")
    def test_invalid_beneficiary_account_validation(self, transfer_api, users):
        payload = transfer_payload(
            from_account_id=users["valid_user"]["account_id"],
            to_account_number="000000000000",
            amount=10,
        )
        response = transfer_api.transfer_funds(payload)

        RequestHelper.assert_status_code(response, 404)
        assert_error_message(response, "beneficiary account not found")

    @pytest.mark.negative
    @pytest.mark.transfer
    @allure.title("Frozen account cannot transfer funds")
    def test_frozen_account_transfer_rejected(self, transfer_api):
        response = transfer_api.transfer_funds(transfer_payload(from_account_id="ACC-FROZEN", amount=10))

        RequestHelper.assert_status_code(response, 403)
        assert_error_message(response, "not active")

    @pytest.mark.negative
    @pytest.mark.transfer
    @allure.title("Transfer request with missing fields is rejected")
    def test_transfer_missing_required_fields(self, transfer_api):
        response = transfer_api.transfer_funds({"from_account_id": "ACC-1001"})

        RequestHelper.assert_status_code(response, 400)
        assert_error_message(response, "required")
