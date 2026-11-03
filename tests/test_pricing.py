"""Tests for pricing, discounts, taxes, and shipping calculations."""

from decimal import Decimal

import pytest

from shopcore.exceptions import InvalidDiscountError, ValidationError
from shopcore.pricing import (
    apply_bulk_discount,
    calculate_item_subtotal,
    calculate_order_totals,
    calculate_shipping,
    calculate_tax,
)


def test_calculate_item_subtotal_basic() -> None:
    subtotal = calculate_item_subtotal(Decimal("19.99"), 3)
    assert subtotal == Decimal("59.97")


def test_calculate_item_subtotal_invalid() -> None:
    with pytest.raises(ValidationError):
        calculate_item_subtotal(Decimal("19.99"), 0)

    with pytest.raises(ValidationError):
        calculate_item_subtotal(Decimal("-5.00"), 2)


def test_apply_bulk_discount_tiers() -> None:
    # Under 10 items -> 0%
    assert apply_bulk_discount(Decimal("100.00"), 5) == Decimal("0.00")
    # 10 items -> 10%
    assert apply_bulk_discount(Decimal("100.00"), 10) == Decimal("10.00")
    # 20 items -> 15%
    assert apply_bulk_discount(Decimal("100.00"), 20) == Decimal("15.00")
    # 50 items -> 20%
    assert apply_bulk_discount(Decimal("100.00"), 50) == Decimal("20.00")


def test_apply_bulk_discount_invalid() -> None:
    with pytest.raises(InvalidDiscountError):
        apply_bulk_discount(Decimal("-10.00"), 10)

    with pytest.raises(ValidationError):
        apply_bulk_discount(Decimal("10.00"), -1)


def test_calculate_tax_standard() -> None:
    # 8% of $100 = $8.00
    tax = calculate_tax(Decimal("100.00"), Decimal("0.08"))
    assert tax == Decimal("8.00")


def test_calculate_shipping_standard() -> None:
    # Base $5.00 + 2kg * $1.50 = $8.00
    shipping = calculate_shipping(Decimal("2.0"))
    assert shipping == Decimal("8.00")


def test_calculate_order_totals_with_discount() -> None:
    # Subtotal 100, Discount 20 -> Taxable 80 -> Tax 8% = 6.40 -> Shipping 5.00 -> Total = 91.40
    res = calculate_order_totals(
        items_subtotal=Decimal("100.00"),
        discount_amount=Decimal("20.00"),
        tax_rate=Decimal("0.08"),
        shipping_fee=Decimal("5.00"),
    )
    assert res["subtotal"] == Decimal("100.00")
    assert res["discount"] == Decimal("20.00")
    assert res["taxable_amount"] == Decimal("80.00")
    assert res["tax"] == Decimal("6.40")
    assert res["shipping"] == Decimal("5.00")
    assert res["total"] == Decimal("91.40")
