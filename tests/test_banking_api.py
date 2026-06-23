import pytest
from api.login_api import LoginAPI
from api.account_api import AccountAPI
from api.beneficiary_api import BeneficiaryAPI
from api.transfer_api import TransferAPI
from api.transaction_api import TransactionAPI


# ---------------------------
# FIXTURES (assumed in conftest)
# ---------------------------
@pytest.fixture
def login_api():
    return LoginAPI()

@pytest.fixture
def account_api():
    return AccountAPI()

@pytest.fixture
def beneficiary_api():
    return BeneficiaryAPI()

@pytest.fixture
def transfer_api():
    return TransferAPI()

@pytest.fixture
def transaction_api():
    return TransactionAPI()


# ===========================
# 🔐 AUTHENTICATION TESTS
# ===========================

def test_valid_login(login_api):
    res = login_api.login("user1", "pass123")
    assert res.status_code == 200
    assert "token" in res.json()


def test_invalid_login(login_api):
    res = login_api.login("wrong", "wrong")
    assert res.status_code == 401


def test_empty_username(login_api):
    res = login_api.login("", "pass123")
    assert res.status_code == 400


def test_empty_password(login_api):
    res = login_api.login("user1", "")
    assert res.status_code == 400


def test_token_generation(login_api):
    res = login_api.login("user1", "pass123")
    assert res.json().get("token") is not None


# ===========================
# 💳 ACCOUNT TESTS
# ===========================

def test_get_account_details(account_api):
    res = account_api.get_account("ACC123")
    assert res.status_code == 200
    assert "account_number" in res.json()


def test_account_balance_validation(account_api):
    res = account_api.get_balance("ACC123")
    assert res.status_code == 200
    assert res.json()["balance"] >= 0


def test_invalid_account_lookup(account_api):
    res = account_api.get_account("INVALID")
    assert res.status_code == 404


def test_account_structure_validation(account_api, json_schema_validator):
    res = account_api.get_account("ACC123")
    assert json_schema_validator.validate("account_schema.json", res.json())


# ===========================
# 👥 BENEFICIARY TESTS
# ===========================

def test_add_beneficiary(beneficiary_api):
    res = beneficiary_api.add({
        "name": "John",
        "account": "ACC999",
        "bank": "HDFC"
    })
    assert res.status_code == 201


def test_duplicate_beneficiary(beneficiary_api):
    data = {"name": "John", "account": "ACC999"}
    beneficiary_api.add(data)
    res = beneficiary_api.add(data)
    assert res.status_code == 409


def test_delete_beneficiary(beneficiary_api):
    beneficiary_api.add({"name": "Mike", "account": "ACC888"})
    res = beneficiary_api.delete("ACC888")
    assert res.status_code == 200


def test_delete_non_existing_beneficiary(beneficiary_api):
    res = beneficiary_api.delete("INVALID")
    assert res.status_code == 404


# ===========================
# 💸 TRANSFER TESTS
# ===========================

def test_successful_transfer(transfer_api):
    res = transfer_api.transfer("ACC123", "ACC456", 500)
    assert res.status_code == 200
    assert res.json()["status"] == "success"


def test_insufficient_balance(transfer_api):
    res = transfer_api.transfer("ACC123", "ACC456", 999999)
    assert res.status_code == 400


def test_invalid_amount_transfer(transfer_api):
    res = transfer_api.transfer("ACC123", "ACC456", -100)
    assert res.status_code == 400


def test_invalid_sender_account(transfer_api):
    res = transfer_api.transfer("INVALID", "ACC456", 100)
    assert res.status_code == 404


def test_invalid_receiver_account(transfer_api):
    res = transfer_api.transfer("ACC123", "INVALID", 100)
    assert res.status_code == 404


def test_zero_amount_transfer(transfer_api):
    res = transfer_api.transfer("ACC123", "ACC456", 0)
    assert res.status_code == 400


# ===========================
# 📊 TRANSACTION TESTS
# ===========================

def test_transaction_history(transaction_api):
    res = transaction_api.get_history("ACC123")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_recent_transactions(transaction_api):
    res = transaction_api.get_recent("ACC123")
    assert res.status_code == 200


def test_transaction_details(transaction_api):
    res = transaction_api.get_transaction("TXN123")
    assert res.status_code == 200
    assert "transaction_id" in res.json()


def test_invalid_transaction_id(transaction_api):
    res = transaction_api.get_transaction("INVALID")
    assert res.status_code == 404


def test_transaction_structure_validation(transaction_api, json_schema_validator):
    res = transaction_api.get_transaction("TXN123")
    assert json_schema_validator.validate("transaction_schema.json", res.json())


# ===========================
# 🔥 EDGE CASE TESTS
# ===========================

def test_large_transfer_amount(transfer_api):
    res = transfer_api.transfer("ACC123", "ACC456", 10**9)
    assert res.status_code in [400, 200]


def test_special_character_account(account_api):
    res = account_api.get_account("@@@###")
    assert res.status_code == 400


def test_null_beneficiary_add(beneficiary_api):
    res = beneficiary_api.add(None)
    assert res.status_code == 400


def test_missing_payload_transfer(transfer_api):
    res = transfer_api.transfer(None, None, None)
    assert res.status_code == 400


def test_multiple_beneficiary_flow(beneficiary_api):
    b1 = beneficiary_api.add({"name": "A", "account": "ACC1"})
    b2 = beneficiary_api.add({"name": "B", "account": "ACC2"})
    assert b1.status_code == 201
    assert b2.status_code == 201