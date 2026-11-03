"""Tests for end-to-end order processing and lifecycle transitions."""

from decimal import Decimal

import pytest

from shopcore.inventory import InventoryItem, InventoryManager
from shopcore.orders import OrderItem, OrderService, OrderStatus
from shopcore.users import UserManager


@pytest.fixture
def test_setup() -> tuple[InventoryManager, UserManager, OrderService]:
    inv = InventoryManager()
    users = UserManager()
    orders = OrderService(inv, users)

    # Seed catalog
    inv.add_item(InventoryItem("SKU-LAPTOP", "Laptop", Decimal("1000.00"), 10))
    inv.add_item(InventoryItem("SKU-MOUSE", "Mouse", Decimal("25.00"), 50))

    # Seed user
    users.register_user("usr-1", "customer@shop.com", "John Doe")

    return inv, users, orders


def test_create_order_success(
    test_setup: tuple[InventoryManager, UserManager, OrderService],
) -> None:
    inv, users, orders = test_setup
    items = [OrderItem("SKU-LAPTOP", 1, Decimal("1000.00"))]

    order = orders.create_order("ORD-001", "usr-1", items)
    assert order.status == OrderStatus.PENDING
    assert order.subtotal == Decimal("1000.00")
    # Subtotal $1000, Tax 8% = $80, Shipping 1kg = $6.50 -> Total = $1086.50
    assert order.total == Decimal("1086.50")

    # Inventory reserved
    laptop = inv.get_item("SKU-LAPTOP")
    assert laptop.reserved_quantity == 1
    assert laptop.available_quantity == 9


def test_confirm_order_flow(
    test_setup: tuple[InventoryManager, UserManager, OrderService],
) -> None:
    inv, users, orders = test_setup
    items = [OrderItem("SKU-MOUSE", 4, Decimal("25.00"))]
    orders.create_order("ORD-002", "usr-1", items)

    confirmed = orders.confirm_order("ORD-002")
    assert confirmed.status == OrderStatus.CONFIRMED

    # Inventory deducted
    mouse = inv.get_item("SKU-MOUSE")
    assert mouse.stock_quantity == 46
    assert mouse.reserved_quantity == 0

    # User awarded loyalty points ($114.50 total -> 11 points)
    user = users.get_user("usr-1")
    assert user.loyalty_points == 11


def test_cancel_pending_order_releases_stock(
    test_setup: tuple[InventoryManager, UserManager, OrderService],
) -> None:
    inv, users, orders = test_setup
    items = [OrderItem("SKU-MOUSE", 5, Decimal("25.00"))]
    orders.create_order("ORD-003", "usr-1", items)

    assert inv.get_item("SKU-MOUSE").reserved_quantity == 5
    orders.cancel_order("ORD-003")

    assert inv.get_item("SKU-MOUSE").reserved_quantity == 0
    assert inv.get_item("SKU-MOUSE").available_quantity == 50
