from datetime import datetime
from decimal import Decimal


def format_amount(amount: Decimal) -> str:
    value = f"{amount:,.2f}".replace(",", " ").replace(".", ",")
    return f"{value} ₽"


def format_dt(dt: datetime) -> str:
    return dt.strftime("%d.%m.%Y %H:%M")
