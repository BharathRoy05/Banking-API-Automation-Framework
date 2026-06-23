import allure
import pytest

from utils.assertions import assert_error_message, assert_money_is_non_negative
from utils.request_helper import RequestHelper


@allure.epic("Digital Banking")
@allure.feature("Accounts")
class TestAccount:
    @pytest.mark.smoke
    @pytest.mark.account
    @pytest.mark.schema
    @allure.title("Customer can retrieve account details")
    def test_account_details_retrieval(self, account_api, users, schemas_dir):
        response = account_api.get_account(users["valid_user"]["account_id"])

        RequestHelper.assert_status_code(response, 200)
        RequestHelper.assert_schema(response, schemas_dir / "account_schema.json")
        assert response.json()["status"] == "ACTIVE"

    @pytest.mark.account
    @allure.title("Customer can list owned accounts")
    def test_list_customer_accounts(self, account_api):
        response = account_api.get_accounts()

        RequestHelper.assert_status_code(response, 200)
        assert len(response.json()["accounts"]) >= 1

    @pytest.mark.account
    @allure.title("Account balance is returned with currency")
    def test_account_balance_validation(self, account_api, users):
        response = account_api.get_balance(users["valid_user"]["account_id"])

        RequestHelper.assert_status_code(response, 200)
        body = response.json()
        assert body["currency"] == "USD"
        assert_money_is_non_negative(body["available_balance"])

    @pytest.mark.negative
    @pytest.mark.account
    @allure.title("Invalid account lookup returns not found")
    def test_invalid_account_lookup(self, account_api):
        response = account_api.get_account("ACC-DOES-NOT-EXIST")

        RequestHelper.assert_status_code(response, 404)
        assert_error_message(response, "account not found")

    @pytest.mark.negative
    @pytest.mark.account
    @allure.title("Invalid balance lookup returns not found")
    def test_invalid_account_balance_lookup(self, account_api):
        response = account_api.get_balance("ACC-404")

        RequestHelper.assert_status_code(response, 404)
        assert_error_message(response, "account not found")

    @pytest.mark.negative
    @pytest.mark.account
    @allure.title("Account endpoint rejects unauthenticated requests")
    def test_account_requires_authentication(self, client, users):
        from api.account_api import AccountAPI

        response = AccountAPI(client).get_account(users["valid_user"]["account_id"])

        RequestHelper.assert_status_code(response, 401)
        assert_error_message(response, "unauthorized")
