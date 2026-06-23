from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from flask import Flask, jsonify, request


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def initial_state() -> dict:
    return {
        "users": {
            "john.doe": {
                "password": "SecurePass123!",
                "customer_id": "CUST-1001",
                "name": "John Doe",
                "account_id": "ACC-1001",
            },
            "jane.smith": {
                "password": "SecurePass456!",
                "customer_id": "CUST-1002",
                "name": "Jane Smith",
                "account_id": "ACC-1002",
            },
        },
        "tokens": {},
        "accounts": {
            "ACC-1001": {
                "account_id": "ACC-1001",
                "customer_id": "CUST-1001",
                "account_type": "SAVINGS",
                "currency": "USD",
                "balance": 7500.75,
                "status": "ACTIVE",
            },
            "ACC-1002": {
                "account_id": "ACC-1002",
                "customer_id": "CUST-1002",
                "account_type": "CHECKING",
                "currency": "USD",
                "balance": 3100.00,
                "status": "ACTIVE",
            },
            "ACC-FROZEN": {
                "account_id": "ACC-FROZEN",
                "customer_id": "CUST-1001",
                "account_type": "SAVINGS",
                "currency": "USD",
                "balance": 100.00,
                "status": "FROZEN",
            },
        },
        "beneficiaries": {
            "CUST-1001": [
                {
                    "beneficiary_id": "BEN-1001",
                    "name": "Jane Smith",
                    "bank_name": "Demo Federal Bank",
                    "account_number": "999900001111",
                    "ifsc": "BANK01234",
                    "nickname": "jane",
                    "created_at": utc_now(),
                }
            ]
        },
        "transactions": {
            "ACC-1001": [
                {
                    "transaction_id": "TXN-1001",
                    "account_id": "ACC-1001",
                    "type": "CREDIT",
                    "amount": 1200.00,
                    "currency": "USD",
                    "status": "SUCCESS",
                    "description": "Salary credit",
                    "created_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
                },
                {
                    "transaction_id": "TXN-1002",
                    "account_id": "ACC-1001",
                    "type": "DEBIT",
                    "amount": 145.50,
                    "currency": "USD",
                    "status": "SUCCESS",
                    "description": "Utility bill payment",
                    "created_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
                },
            ],
            "ACC-1002": [],
        },
    }


STATE = initial_state()


def create_app() -> Flask:
    app = Flask(__name__)

    @app.post("/test/reset")
    def reset_state():
        global STATE
        STATE = initial_state()
        return jsonify({"message": "state reset"}), 200

    @app.get("/health")
    def health():
        return jsonify({"status": "UP", "service": "mock-banking-api"}), 200

    @app.post("/auth/login")
    def login():
        payload = request.get_json(silent=True) or {}
        username = payload.get("username")
        password = payload.get("password")
        if not username or not password:
            return jsonify({"error": "username and password are required"}), 400

        user = STATE["users"].get(username)
        if not user or user["password"] != password:
            return jsonify({"error": "invalid username or password"}), 401

        token = f"mock-token-{uuid4().hex}"
        STATE["tokens"][token] = {
            "username": username,
            "customer_id": user["customer_id"],
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        return jsonify(
            {
                "token": token,
                "token_type": "Bearer",
                "expires_in": 3600,
                "customer": {
                    "customer_id": user["customer_id"],
                    "name": user["name"],
                    "username": username,
                },
            }
        ), 200

    @app.get("/auth/validate")
    def validate_token():
        auth = request.headers.get("Authorization", "")
        token = auth.replace("Bearer ", "", 1)
        token_data = STATE["tokens"].get(token)
        if not token_data:
            return jsonify({"valid": False, "error": "invalid or missing token"}), 401
        if token_data["expires_at"] < datetime.now(timezone.utc):
            return jsonify({"valid": False, "error": "token expired"}), 401
        return jsonify({"valid": True, "customer_id": token_data["customer_id"]}), 200

    @app.get("/accounts")
    @require_auth
    def accounts(current_user):
        owned_accounts = [
            account for account in STATE["accounts"].values() if account["customer_id"] == current_user["customer_id"]
        ]
        return jsonify({"accounts": owned_accounts}), 200

    @app.get("/accounts/<account_id>")
    @require_auth
    def account_details(current_user, account_id):
        account = STATE["accounts"].get(account_id)
        if not account or account["customer_id"] != current_user["customer_id"]:
            return jsonify({"error": "account not found"}), 404
        return jsonify(account), 200

    @app.get("/accounts/<account_id>/balance")
    @require_auth
    def account_balance(current_user, account_id):
        account = STATE["accounts"].get(account_id)
        if not account or account["customer_id"] != current_user["customer_id"]:
            return jsonify({"error": "account not found"}), 404
        return jsonify(
            {
                "account_id": account["account_id"],
                "currency": account["currency"],
                "available_balance": account["balance"],
                "status": account["status"],
            }
        ), 200

    @app.get("/beneficiaries")
    @require_auth
    def list_beneficiaries(current_user):
        return jsonify({"beneficiaries": STATE["beneficiaries"].get(current_user["customer_id"], [])}), 200

    @app.post("/beneficiaries")
    @require_auth
    def add_beneficiary(current_user):
        payload = request.get_json(silent=True) or {}
        required = ["name", "bank_name", "account_number", "ifsc", "nickname"]
        missing = [field for field in required if not payload.get(field)]
        if missing:
            return jsonify({"error": "missing required fields", "fields": missing}), 400

        beneficiaries = STATE["beneficiaries"].setdefault(current_user["customer_id"], [])
        duplicate = any(item["account_number"] == payload["account_number"] for item in beneficiaries)
        if duplicate:
            return jsonify({"error": "beneficiary already exists"}), 409

        beneficiary = deepcopy(payload)
        beneficiary["beneficiary_id"] = f"BEN-{uuid4().hex[:8].upper()}"
        beneficiary["created_at"] = utc_now()
        beneficiaries.append(beneficiary)
        return jsonify(beneficiary), 201

    @app.delete("/beneficiaries/<beneficiary_id>")
    @require_auth
    def delete_beneficiary(current_user, beneficiary_id):
        beneficiaries = STATE["beneficiaries"].setdefault(current_user["customer_id"], [])
        for index, beneficiary in enumerate(beneficiaries):
            if beneficiary["beneficiary_id"] == beneficiary_id:
                beneficiaries.pop(index)
                return jsonify({"message": "beneficiary deleted"}), 200
        return jsonify({"error": "beneficiary not found"}), 404

    @app.post("/transfers")
    @require_auth
    def transfer(current_user):
        payload = request.get_json(silent=True) or {}
        from_account_id = payload.get("from_account_id")
        to_account_number = payload.get("to_account_number")
        amount = payload.get("amount")
        if not from_account_id or not to_account_number or amount is None:
            return jsonify({"error": "from_account_id, to_account_number and amount are required"}), 400
        if not isinstance(amount, (int, float)) or amount <= 0:
            return jsonify({"error": "amount must be greater than zero"}), 400

        account = STATE["accounts"].get(from_account_id)
        if not account or account["customer_id"] != current_user["customer_id"]:
            return jsonify({"error": "source account not found"}), 404
        if account["status"] != "ACTIVE":
            return jsonify({"error": "source account is not active"}), 403
        if amount > account["balance"]:
            return jsonify({"error": "insufficient balance"}), 422

        beneficiaries = STATE["beneficiaries"].get(current_user["customer_id"], [])
        beneficiary = next((item for item in beneficiaries if item["account_number"] == to_account_number), None)
        if not beneficiary:
            return jsonify({"error": "beneficiary account not found"}), 404

        account["balance"] = round(account["balance"] - float(amount), 2)
        transaction = {
            "transaction_id": f"TXN-{uuid4().hex[:10].upper()}",
            "account_id": from_account_id,
            "type": "DEBIT",
            "amount": float(amount),
            "currency": payload.get("currency", account["currency"]),
            "status": "SUCCESS",
            "description": payload.get("remarks", f"Transfer to {beneficiary['name']}"),
            "created_at": utc_now(),
        }
        STATE["transactions"].setdefault(from_account_id, []).insert(0, transaction)
        return jsonify({"message": "transfer successful", "transaction": transaction, "balance": account["balance"]}), 201

    @app.get("/accounts/<account_id>/transactions")
    @require_auth
    def transaction_history(current_user, account_id):
        account = STATE["accounts"].get(account_id)
        if not account or account["customer_id"] != current_user["customer_id"]:
            return jsonify({"error": "account not found"}), 404
        transactions = STATE["transactions"].get(account_id, [])
        limit = request.args.get("limit", type=int)
        if limit is not None:
            transactions = transactions[:limit]
        return jsonify({"account_id": account_id, "transactions": transactions}), 200

    @app.get("/accounts/<account_id>/transactions/recent")
    @require_auth
    def recent_transactions(current_user, account_id):
        account = STATE["accounts"].get(account_id)
        if not account or account["customer_id"] != current_user["customer_id"]:
            return jsonify({"error": "account not found"}), 404
        return jsonify({"account_id": account_id, "transactions": STATE["transactions"].get(account_id, [])[:5]}), 200

    @app.get("/transactions/<transaction_id>")
    @require_auth
    def transaction_details(current_user, transaction_id):
        owned_account_ids = {
            account_id
            for account_id, account in STATE["accounts"].items()
            if account["customer_id"] == current_user["customer_id"]
        }
        for account_id, transactions in STATE["transactions"].items():
            if account_id not in owned_account_ids:
                continue
            for transaction in transactions:
                if transaction["transaction_id"] == transaction_id:
                    return jsonify(transaction), 200
        return jsonify({"error": "transaction not found"}), 404

    return app


def require_auth(view):
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        token = auth.replace("Bearer ", "", 1)
        token_data = STATE["tokens"].get(token)
        if not token_data:
            return jsonify({"error": "unauthorized"}), 401
        if token_data["expires_at"] < datetime.now(timezone.utc):
            return jsonify({"error": "token expired"}), 401
        return view(token_data, *args, **kwargs)

    wrapper.__name__ = view.__name__
    return wrapper


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
