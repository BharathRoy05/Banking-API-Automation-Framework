import allure
import pytest

from api.login_api import LoginAPI
from utils.assertions import assert_error_message
from utils.request_helper import RequestHelper


@allure.epic("Digital Banking")
@allure.feature("Authentication")
class TestLogin:
    @pytest.mark.smoke
    @pytest.mark.auth
    @pytest.mark.schema
    @allure.title("Valid customer can log in and receive bearer token")
    def test_valid_login(self, login_api, users, schemas_dir):
        user = users["valid_user"]
        response = login_api.login(user["username"], user["password"])

        RequestHelper.assert_status_code(response, 200)
        RequestHelper.assert_schema(response, schemas_dir / "login_schema.json")
        assert response.json()["customer"]["customer_id"] == user["customer_id"]

    @pytest.mark.negative
    @pytest.mark.auth
    @allure.title("Invalid credentials are rejected")
    def test_invalid_login(self, login_api, users):
        user = users["invalid_user"]
        response = login_api.login(user["username"], user["password"])

        RequestHelper.assert_status_code(response, 401)
        assert_error_message(response, "invalid username or password")

    @pytest.mark.negative
    @pytest.mark.auth
    @pytest.mark.parametrize(
        "username,password",
        [
            ("", ""),
            ("john.doe", ""),
            ("", "SecurePass123!"),
            (None, None),
        ],
    )
    @allure.title("Empty credentials are validated")
    def test_empty_credentials(self, login_api, username, password):
        response = login_api.login(username, password)

        RequestHelper.assert_status_code(response, 400)
        assert_error_message(response, "required")

    @pytest.mark.smoke
    @pytest.mark.auth
    @allure.title("Issued token can be validated")
    def test_token_validation(self, client, users):
        login_api = LoginAPI(client)
        user = users["valid_user"]
        login_response = login_api.login(user["username"], user["password"])
        token = login_response.json()["token"]

        response = login_api.validate_token(token)

        RequestHelper.assert_status_code(response, 200)
        assert response.json()["valid"] is True
        assert response.json()["customer_id"] == user["customer_id"]

    @pytest.mark.negative
    @pytest.mark.auth
    @allure.title("Missing token is rejected")
    def test_missing_token_validation(self, login_api):
        response = login_api.validate_token()

        RequestHelper.assert_status_code(response, 401)
        assert response.json()["valid"] is False

    @pytest.mark.negative
    @pytest.mark.auth
    @allure.title("Tampered token is rejected")
    def test_invalid_token_validation(self, login_api):
        response = login_api.validate_token("tampered-token")

        RequestHelper.assert_status_code(response, 401)
        assert response.json()["valid"] is False
