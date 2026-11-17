"""Pricing and discount calculation business logic."""

from decimal import ROUND_HALF_UP, Decimal

from shopcore.exceptions import InvalidDiscountError, ValidationError

DEFAULT_TAX_RATE = Decimal("0.08")
DEFAULT_SHIPPING_BASE = Decimal("5.00")
DEFAULT_SHIPPING_PER_KG = Decimal("1.50")


def quantize_currency(amount: Decimal) -> Decimal:
    """Quantize decimal value to 2 decimal places using standard ROUND_HALF_UP."""
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_item_subtotal(unit_price: Decimal, quantity: int) -> Decimal:
    """Calculate the subtotal for a given line item quantity.

    Args:
        unit_price: Price per individual unit.
        quantity: Number of units purchased.

    Returns:
        Subtotal rounded to 2 decimal places.

    Raises:
        ValidationError: If quantity is less than or equal to zero or price is negative.
    """
    if quantity <= 0:
        raise ValidationError(f"Quantity must be positive, got {quantity}")
    if unit_price < Decimal("0.00"):
        raise ValidationError(f"Unit price cannot be negative, got {unit_price}")

    return quantize_currency(unit_price * Decimal(quantity))


def apply_bulk_discount(subtotal: Decimal, item_count: int) -> Decimal:
    """Calculate the bulk order discount amount based on total item quantity.

    Tier rules:
    - Over 50 items: 20% discount
    - Over 20 items: 15% discount
    - Over 10 items: 10% discount
    - 10 or fewer items: 0% discount

    Args:
        subtotal: Pre-discount subtotal.
        item_count: Total units in order.

    Returns:
        Discount amount to deduct.
    """
    if subtotal < Decimal("0.00"):
        raise InvalidDiscountError("Subtotal cannot be negative")
    if item_count < 0:
        raise ValidationError(f"Item count cannot be negative, got {item_count}")

    if item_count > 50:
        rate = Decimal("0.20")
    elif item_count > 20:
        rate = Decimal("0.15")
    elif item_count > 10:
        rate = Decimal("0.10")
    else:
        rate = Decimal("0.00")

    return quantize_currency(subtotal * rate)


def calculate_tax(taxable_amount: Decimal, tax_rate: Decimal = DEFAULT_TAX_RATE) -> Decimal:
    """Calculate sales tax on the taxable amount.

    Args:
        taxable_amount: Net amount subject to tax.
        tax_rate: Tax rate percentage as decimal.

    Returns:
        Calculated tax rounded to 2 decimal places.
    """
    if taxable_amount < Decimal("0.00"):
        raise ValidationError("Taxable amount cannot be negative")
    if tax_rate < Decimal("0.00"):
        raise ValidationError("Tax rate cannot be negative")

    return quantize_currency(taxable_amount * tax_rate)


def calculate_shipping(
    weight_kg: Decimal,
    base_rate: Decimal = DEFAULT_SHIPPING_BASE,
    per_kg_rate: Decimal = DEFAULT_SHIPPING_PER_KG,
) -> Decimal:
    """Calculate shipping cost based on package weight.

    Args:
        weight_kg: Total parcel weight in kilograms.
        base_rate: Base flat rate fee.
        per_kg_rate: Incremental fee per kg.

    Returns:
        Total shipping fee.
    """
    if weight_kg < Decimal("0.00"):
        raise ValidationError("Weight cannot be negative")

    return quantize_currency(base_rate + (weight_kg * per_kg_rate))


def calculate_order_totals(
    items_subtotal: Decimal,
    discount_amount: Decimal,
    tax_rate: Decimal = DEFAULT_TAX_RATE,
    shipping_fee: Decimal = Decimal("0.00"),
) -> dict[str, Decimal]:
    """Calculate final order financial totals including net taxable amount, tax, and grand total.

    Args:
        items_subtotal: Gross subtotal of all items.
        discount_amount: Total discount amount.
        tax_rate: Tax rate to apply.
        shipping_fee: Shipping cost.

    Returns:
        Dictionary with subtotal, discount, taxable_amount, tax, shipping, and total.
    """
    if items_subtotal < Decimal("0.00"):
        raise ValidationError("Subtotal cannot be negative")
    if discount_amount < Decimal("0.00"):
        raise InvalidDiscountError("Discount amount cannot be negative")

    taxable_amount = quantize_currency(items_subtotal - discount_amount)
    tax = calculate_tax(items_subtotal, tax_rate)
    total = quantize_currency(taxable_amount + tax + shipping_fee)

    return {
        "subtotal": quantize_currency(items_subtotal),
        "discount": quantize_currency(discount_amount),
        "taxable_amount": taxable_amount,
        "tax": tax,
        "shipping": quantize_currency(shipping_fee),
        "total": total,
    }
    
def calculate_average_discount(discounts: list[Decimal]) -> Decimal:
    """Calculate mean discount, unhandled for empty input."""
    return sum(discounts) / len(discounts)