from __future__ import annotations

import argparse
import os
import sys
from typing import Callable, TypeVar

from bot.client import BinanceFuturesClient
from bot.exceptions import APIError, NetworkError, ValidationError
from bot.logging_config import setup_logging
from bot.orders import OrderRequest, OrderService
from bot.validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_symbol,
)

T = TypeVar("T")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Place Binance Futures Testnet orders (USDT-M).",
    )
    parser.add_argument("--symbol", help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side", help="BUY or SELL")
    parser.add_argument("--order-type", help="MARKET or LIMIT")
    parser.add_argument("--quantity", help="Order quantity")
    parser.add_argument("--price", help="Limit price (required for LIMIT orders)")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for missing required inputs.",
    )
    return parser.parse_args()


def prompt_if_missing(value: str | None, label: str) -> str:
    return value if value else input(f"Enter {label}: ").strip()


def prompt_and_validate(
    value: str | None,
    label: str,
    validator: Callable[[str], T],
) -> T:
    while True:
        candidate = prompt_if_missing(value, label)
        try:
            return validator(candidate)
        except ValidationError as exc:
            print(f"Invalid {label}: {exc}")
            value = None


def run() -> int:
    args = parse_args()
    logger = setup_logging()
    client: BinanceFuturesClient | None = None

    try:
        symbol = args.symbol
        side = args.side
        order_type = args.order_type
        quantity = args.quantity
        price = args.price

        missing = [name for name, val in [("symbol", symbol), ("side", side), ("order type", order_type), ("quantity", quantity)] if not val]
        if missing and not args.interactive:
            raise ValidationError(
                f"Missing required inputs: {', '.join(missing)}. "
                "Use --interactive to be prompted."
            )

        if args.interactive:
            symbol = prompt_and_validate(symbol, "symbol (e.g., BTCUSDT)", validate_symbol)
            side = prompt_and_validate(side, "side (BUY/SELL)", validate_side)
            order_type = prompt_and_validate(
                order_type,
                "order type (MARKET/LIMIT)",
                validate_order_type,
            )
            quantity_value = prompt_and_validate(quantity, "quantity", validate_quantity)
        else:
            symbol = validate_symbol(symbol)
            side = validate_side(side)
            order_type = validate_order_type(order_type)
            quantity_value = validate_quantity(quantity)

        price_value = None
        if order_type == "LIMIT":
            if args.interactive:
                price_value = prompt_and_validate(price, "price", validate_price)
            else:
                price_value = validate_price(price)

        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")
        if not api_key or not api_secret:
            raise ValidationError(
                "Missing API credentials. Set BINANCE_API_KEY and BINANCE_API_SECRET."
            )

        client = BinanceFuturesClient(api_key=api_key, api_secret=api_secret, logger=logger)
        service = OrderService(client)

        order = OrderRequest(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity_value,
            price=price_value,
        )

        print("Order Request Summary")
        print(f"symbol: {order.symbol}")
        print(f"side: {order.side}")
        print(f"type: {order.order_type}")
        print(f"quantity: {order.quantity}")
        if order.price is not None:
            print(f"price: {order.price}")

        result = service.place_order(order)

        print("\nOrder Response Details")
        print(f"orderId: {result.get('orderId')}")
        print(f"status: {result.get('status')}")
        print(f"executedQty: {result.get('executedQty')}")
        if result.get("avgPrice") not in (None, "", "0"):
            print(f"avgPrice: {result.get('avgPrice')}")

        print("\nResult: SUCCESS - Order placed on Binance Futures Testnet.")
        return 0

    except ValidationError as exc:
        logger.error("validation_error %s", str(exc))
        print(f"Result: FAILURE - Validation error: {exc}")
        return 2
    except APIError as exc:
        logger.error("api_error %s", str(exc))
        print(f"Result: FAILURE - Binance API error: {exc}")
        return 3
    except NetworkError as exc:
        logger.error("network_error %s", str(exc))
        print(f"Result: FAILURE - Network error: {exc}")
        return 4
    except KeyboardInterrupt:
        print("Result: FAILURE - Cancelled by user.")
        return 130
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    sys.exit(run())

