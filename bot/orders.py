from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from bot.client import BinanceFuturesClient
from bot.exceptions import ValidationError
from bot.validators import format_decimal


@dataclass(slots=True)
class OrderRequest:
    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    price: Decimal | None = None


class OrderService:
    def __init__(self, client: BinanceFuturesClient):
        self.client = client

    def place_order(self, order: OrderRequest) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "symbol": order.symbol,
            "side": order.side,
            "type": order.order_type,
            "quantity": format_decimal(order.quantity),
        }
        if order.order_type == "LIMIT":
            if order.price is None:
                raise ValidationError("Price is required for LIMIT orders.")
            payload["price"] = format_decimal(order.price)
            payload["timeInForce"] = "GTC"

        response = self.client.place_order(payload)
        return {
            "orderId": response.get("orderId"),
            "status": response.get("status"),
            "executedQty": response.get("executedQty"),
            "avgPrice": response.get("avgPrice"),
            "raw": response,
        }

