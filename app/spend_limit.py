from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


MAX_SPEND_LIMIT = Decimal("1000000.00")


def parse_spend_limit(value):
    try:
        amount = Decimal(value.strip())
    except (AttributeError, InvalidOperation):
        raise ValueError("Enter a valid spending limit.") from None

    if not amount.is_finite():
        raise ValueError("Enter a valid spending limit.")

    if amount <= 0:
        raise ValueError("Spending limit must be greater than zero.")

    if amount > MAX_SPEND_LIMIT:
        raise ValueError("Spending limit must be $1,000,000 or less.")

    amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if amount <= 0:
        raise ValueError("Spending limit must be greater than zero.")

    return int(amount * 100)


def format_spend_limit(spend_limit_cents):
    dollars, cents = divmod(spend_limit_cents, 100)
    return f"${dollars:,}.{cents:02d}"


def spend_limit_input_value(spend_limit_cents):
    dollars, cents = divmod(spend_limit_cents, 100)
    return f"{dollars}.{cents:02d}"
