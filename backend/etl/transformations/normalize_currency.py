from decimal import Decimal

def clean_amount_str(amount: str) -> Decimal:
    if amount is None:
        return Decimal(0)
    return Decimal(str(amount).replace(",", "").strip())
