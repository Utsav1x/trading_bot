from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from bot.exceptions import ValidationError

SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{4,20}$")
VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}


def validate_symbol(symbol: str) -> str:
    value = (symbol or "").strip().upper()
    if not value or not SYMBOL_PATTERN.match(value):
        raise ValidationError("Invalid symbol. Example: BTCUSDT")
    return value


def validate_side(side: str) -> str:
    value = (side or "").strip().upper()
    if value not in VALID_SIDES:
        raise ValidationError("Invalid side. Use BUY or SELL.")
    return value


def validate_order_type(order_type: str) -> str:
    value = (order_type or "").strip().upper()
    if value not in VALID_ORDER_TYPES:
        raise ValidationError("Invalid order type. Use MARKET or LIMIT.")
    return value


def validate_quantity(quantity: str | float | int | Decimal) -> Decimal:
    try:
        value = Decimal(str(quantity))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValidationError("Invalid quantity. Use a positive number.") from exc

    if value <= 0:
        raise ValidationError("Invalid quantity. Quantity must be greater than 0.")
    return value


def validate_price(price: str | float | int | Decimal | None) -> Decimal:
    if price is None or str(price).strip() == "":
        raise ValidationError("Price is required for LIMIT orders.")
    try:
        value = Decimal(str(price))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValidationError("Invalid price. Use a positive number.") from exc

    if value <= 0:
        raise ValidationError("Invalid price. Price must be greater than 0.")
    return value


def format_decimal(value: Decimal) -> str:
    normalized = value.normalize()
    text = format(normalized, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text

