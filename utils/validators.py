from datetime import date, datetime
from decimal import Decimal, InvalidOperation

MAX_EXPENSE_AMOUNT = Decimal("9999999999.99")


def normalize_category_name(value: str) -> str:
    return " ".join((value or "").strip().split())


def make_category_key(value: str) -> str:
    return normalize_category_name(value).casefold()


def parse_amount(value: str) -> Decimal:
    raw_value = (value or "").strip()
    if not raw_value:
        raise ValueError("Введите сумму. Например: 450 или 450.75")

    normalized = raw_value.replace(" ", "").replace(",", ".")
    if normalized.count(".") > 1:
        raise ValueError("Сумма указана в неверном формате. Пример: 450.75")

    try:
        amount = Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError(
            "Не удалось распознать сумму. Используйте только цифры и разделитель '.' или ','."
        ) from exc

    if amount <= 0:
        raise ValueError("Сумма должна быть больше нуля.")

    amount = amount.quantize(Decimal("0.01"))
    if amount > MAX_EXPENSE_AMOUNT:
        raise ValueError("Сумма слишком большая для сохранения.")

    return amount


def parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None
