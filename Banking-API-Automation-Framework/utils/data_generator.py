from decimal import Decimal

from faker import Faker


fake = Faker()


def beneficiary_payload(account_number: str | None = None, nickname: str | None = None) -> dict:
    return {
        "name": fake.name(),
        "bank_name": fake.company() + " Bank",
        "account_number": account_number or fake.bban(),
        "ifsc": fake.bothify(text="BANK0####"),
        "nickname": nickname or fake.first_name().lower(),
    }


def transfer_payload(
    from_account_id: str = "ACC-1001",
    to_account_number: str = "999900001111",
    amount: float | Decimal = 100.00,
    remarks: str | None = None,
) -> dict:
    return {
        "from_account_id": from_account_id,
        "to_account_number": to_account_number,
        "amount": float(amount),
        "currency": "USD",
        "remarks": remarks or f"Automation transfer {fake.pyint(min_value=1000, max_value=9999)}",
    }
