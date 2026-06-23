import allure
import pytest

from utils.assertions import assert_error_message
from utils.data_generator import beneficiary_payload
from utils.request_helper import RequestHelper


@allure.epic("Digital Banking")
@allure.feature("Beneficiaries")
class TestBeneficiary:
    @pytest.mark.smoke
    @pytest.mark.beneficiary
    @allure.title("Customer can add a new beneficiary")
    def test_add_beneficiary(self, beneficiary_api):
        payload = beneficiary_payload(account_number="888877776666", nickname="newpayee")
        response = beneficiary_api.add_beneficiary(payload)

        RequestHelper.assert_status_code(response, 201)
        assert response.json()["account_number"] == payload["account_number"]
        assert response.json()["beneficiary_id"].startswith("BEN-")

    @pytest.mark.beneficiary
    @allure.title("Customer can list beneficiaries")
    def test_list_beneficiaries(self, beneficiary_api):
        response = beneficiary_api.list_beneficiaries()

        RequestHelper.assert_status_code(response, 200)
        assert isinstance(response.json()["beneficiaries"], list)

    @pytest.mark.beneficiary
    @allure.title("Customer can delete a beneficiary")
    def test_delete_beneficiary(self, beneficiary_api):
        create_response = beneficiary_api.add_beneficiary(beneficiary_payload(account_number="777766665555"))
        beneficiary_id = create_response.json()["beneficiary_id"]

        response = beneficiary_api.delete_beneficiary(beneficiary_id)

        RequestHelper.assert_status_code(response, 200)
        assert response.json()["message"] == "beneficiary deleted"

    @pytest.mark.negative
    @pytest.mark.beneficiary
    @allure.title("Duplicate beneficiary is rejected")
    def test_duplicate_beneficiary_validation(self, beneficiary_api):
        payload = beneficiary_payload(account_number="123412341234", nickname="repeat")
        first_response = beneficiary_api.add_beneficiary(payload)
        duplicate_response = beneficiary_api.add_beneficiary(payload)

        RequestHelper.assert_status_code(first_response, 201)
        RequestHelper.assert_status_code(duplicate_response, 409)
        assert_error_message(duplicate_response, "already exists")

    @pytest.mark.negative
    @pytest.mark.beneficiary
    @allure.title("Adding beneficiary with missing fields is rejected")
    def test_add_beneficiary_missing_required_fields(self, beneficiary_api):
        response = beneficiary_api.add_beneficiary({"name": "Incomplete Payee"})

        RequestHelper.assert_status_code(response, 400)
        assert_error_message(response, "missing required fields")

    @pytest.mark.negative
    @pytest.mark.beneficiary
    @allure.title("Deleting unknown beneficiary returns not found")
    def test_delete_unknown_beneficiary(self, beneficiary_api):
        response = beneficiary_api.delete_beneficiary("BEN-UNKNOWN")

        RequestHelper.assert_status_code(response, 404)
        assert_error_message(response, "beneficiary not found")
