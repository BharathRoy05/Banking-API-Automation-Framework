import allure
import pytest

from utils.assertions import assert_collection_not_empty, assert_error_message
from utils.data_generator import transfer_payload
from utils.request_helper import RequestHelper


@allure.epic("Digital Banking")
@allure.feature("Transactions")
class TestTransaction:
    @pytest.mark.smoke
    @pytest.mark.transaction
    @allure.title("Customer can retrieve transaction history")
    def test_transaction_history(self, transaction_api, users):
        response = transaction_api.get_transactions(users["valid_user"]["account_id"])

        RequestHelper.assert_status_code(response, 200)
        assert_collection_not_empty(response.json()["transactions"], "transactions")

    @pytest.mark.transaction
    @pytest.mark.schema
    @allure.title("Customer can retrieve transaction details")
    def test_transaction_details(self, transaction_api, users, schemas_dir):
        history = transaction_api.get_transactions(users["valid_user"]["account_id"]).json()["transactions"]
        transaction_id = history[0]["transaction_id"]
        response = transaction_api.get_transaction_details(transaction_id)

        RequestHelper.assert_status_code(response, 200)
        RequestHelper.assert_schema(response, schemas_dir / "transaction_schema.json")
        assert response.json()["transaction_id"] == transaction_id

    @pytest.mark.transaction
    @allure.title("Recent transactions endpoint returns latest transactions")
    def test_recent_transactions_validation(self, transaction_api, users):
        response = transaction_api.get_recent_transactions(users["valid_user"]["account_id"])

        RequestHelper.assert_status_code(response, 200)
        assert len(response.json()["transactions"]) <= 5

    @pytest.mark.transaction
    @allure.title("Transaction history supports limit parameter")
    def test_transaction_history_limit(self, transaction_api, users):
        response = transaction_api.get_transactions(users["valid_user"]["account_id"], limit=1)

        RequestHelper.assert_status_code(response, 200)
        assert len(response.json()["transactions"]) == 1

    @pytest.mark.transaction
    @allure.title("Successful transfer appears in recent transaction history")
    def test_transfer_appears_in_recent_transactions(self, transfer_api, transaction_api, users):
        account_id = users["valid_user"]["account_id"]
        transfer_api.transfer_funds(transfer_payload(from_account_id=account_id, amount=25.0))
        response = transaction_api.get_recent_transactions(account_id)

        RequestHelper.assert_status_code(response, 200)
        assert response.json()["transactions"][0]["amount"] == 25.0

    @pytest.mark.negative
    @pytest.mark.transaction
    @allure.title("Unknown transaction details return not found")
    def test_unknown_transaction_details(self, transaction_api):
        response = transaction_api.get_transaction_details("TXN-NOT-FOUND")

        RequestHelper.assert_status_code(response, 404)
        assert_error_message(response, "transaction not found")

    @pytest.mark.negative
    @pytest.mark.transaction
    @allure.title("Transaction history rejects invalid account")
    def test_transaction_history_invalid_account(self, transaction_api):
        response = transaction_api.get_transactions("ACC-NOT-FOUND")

        RequestHelper.assert_status_code(response, 404)
        assert_error_message(response, "account not found")
