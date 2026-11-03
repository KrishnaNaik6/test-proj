"""Tests for inventory management and stock reservations."""

from decimal import Decimal

import pytest

from shopcore.exceptions import (
    InsufficientStockError,
    ItemNotFoundError,
)
from shopcore.inventory import InventoryItem, InventoryManager


def test_add_and_get_item() -> None:
    inv = InventoryManager()
    item = InventoryItem(
        sku="SKU-100",
        name="Wireless Keyboard",
        unit_price=Decimal("49.99"),
        stock_quantity=20,
    )
    inv.add_item(item)
    fetched = inv.get_item("SKU-100")
    assert fetched.name == "Wireless Keyboard"
    assert fetched.available_quantity == 20


def test_get_nonexistent_item() -> None:
    inv = InventoryManager()
    with pytest.raises(ItemNotFoundError):
        inv.get_item("NONEXISTENT")


def test_reserve_and_release_stock() -> None:
    inv = InventoryManager()
    inv.add_item(InventoryItem("SKU-100", "Mouse", Decimal("15.00"), 10))
    inv.reserve_stock("SKU-100", 3)
    item = inv.get_item("SKU-100")
    assert item.reserved_quantity == 3
    assert item.available_quantity == 7

    inv.release_stock("SKU-100", 2)
    assert item.reserved_quantity == 1
    assert item.available_quantity == 9


def test_insufficient_stock_error() -> None:
    inv = InventoryManager()
    inv.add_item(InventoryItem("SKU-100", "Mouse", Decimal("15.00"), 5))
    with pytest.raises(InsufficientStockError):
        inv.reserve_stock("SKU-100", 10)


def test_deduct_and_restock() -> None:
    inv = InventoryManager()
    inv.add_item(InventoryItem("SKU-100", "Monitor", Decimal("199.00"), 10))
    inv.reserve_stock("SKU-100", 4)
    inv.deduct_stock("SKU-100", 4)
    item = inv.get_item("SKU-100")
    assert item.stock_quantity == 6
    assert item.reserved_quantity == 0

    inv.restock("SKU-100", 5)
    assert item.stock_quantity == 11


def test_batch_reserve_success() -> None:
    inv = InventoryManager()
    inv.add_item(InventoryItem("SKU-A", "Item A", Decimal("10.00"), 10))
    inv.add_item(InventoryItem("SKU-B", "Item B", Decimal("20.00"), 5))
    inv.batch_reserve([("SKU-A", 4), ("SKU-B", 2)])
    assert inv.get_item("SKU-A").available_quantity == 6
    assert inv.get_item("SKU-B").available_quantity == 3


def test_batch_reserve_atomic_rollback() -> None:
    inv = InventoryManager()
    inv.add_item(InventoryItem("SKU-A", "Item A", Decimal("10.00"), 5))
    inv.add_item(InventoryItem("SKU-B", "Item B", Decimal("20.00"), 2))

    with pytest.raises(InsufficientStockError):
        # SKU-A would succeed, but SKU-B requests 10 which exceeds 2
        inv.batch_reserve([("SKU-A", 3), ("SKU-B", 10)])

    # Ensure SKU-A reservation was rolled back
    assert inv.get_item("SKU-A").reserved_quantity == 0
    assert inv.get_item("SKU-A").available_quantity == 5


def test_get_low_stock_items() -> None:
    inv = InventoryManager()
    # Available = 10, threshold = 5 -> not low
    inv.add_item(InventoryItem("SKU-1", "Item 1", Decimal("5.00"), 10, reorder_threshold=5))
    # Available = 3, threshold = 5 -> low
    inv.add_item(InventoryItem("SKU-2", "Item 2", Decimal("5.00"), 3, reorder_threshold=5))
    # Available = 10 - 7 = 3, threshold = 5 -> low
    item3 = InventoryItem("SKU-3", "Item 3", Decimal("5.00"), 10, reorder_threshold=5)
    inv.add_item(item3)
    inv.reserve_stock("SKU-3", 7)

    low = inv.get_low_stock_items()
    low_skus = {i.sku for i in low}
    assert "SKU-2" in low_skus
    assert "SKU-3" in low_skus
    assert "SKU-1" not in low_skus
