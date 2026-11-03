"""Inventory management and stock tracking logic."""

from dataclasses import dataclass
from decimal import Decimal

from shopcore.exceptions import (
    InsufficientStockError,
    InventoryError,
    ItemNotFoundError,
    ValidationError,
)


@dataclass
class InventoryItem:
    """Represents a product item in inventory."""

    sku: str
    name: str
    unit_price: Decimal
    stock_quantity: int
    reserved_quantity: int = 0
    reorder_threshold: int = 5

    @property
    def available_quantity(self) -> int:
        """Quantity available for purchase (on-hand minus reserved)."""
        return max(0, self.stock_quantity - self.reserved_quantity)


class InventoryManager:
    """Manages catalog items, reservations, deductions, and restocks."""

    def __init__(self) -> None:
        self._items: dict[str, InventoryItem] = {}

    def add_item(self, item: InventoryItem) -> None:
        """Register a new inventory item in the catalog."""
        if not item.sku or not item.sku.strip():
            raise ValidationError("SKU cannot be empty")
        if item.sku in self._items:
            raise InventoryError(f"Item with SKU '{item.sku}' already exists")
        if item.stock_quantity < 0:
            raise ValidationError("Initial stock quantity cannot be negative")
        self._items[item.sku] = item

    def get_item(self, sku: str) -> InventoryItem:
        """Fetch item by SKU.

        Raises:
            ItemNotFoundError: If SKU is not registered.
        """
        if sku not in self._items:
            raise ItemNotFoundError(f"Item with SKU '{sku}' not found")
        return self._items[sku]

    def reserve_stock(self, sku: str, quantity: int) -> None:
        """Reserve a quantity of an item for an order."""
        if quantity <= 0:
            raise ValidationError(f"Reservation quantity must be positive, got {quantity}")
        item = self.get_item(sku)
        if item.available_quantity < quantity:
            msg = (
                f"Cannot reserve {quantity} of SKU '{sku}': "
                f"only {item.available_quantity} available"
            )
            raise InsufficientStockError(msg)
        item.reserved_quantity += quantity

    def release_stock(self, sku: str, quantity: int) -> None:
        """Release previously reserved stock back to available pool."""
        if quantity <= 0:
            raise ValidationError(f"Release quantity must be positive, got {quantity}")
        item = self.get_item(sku)
        if item.reserved_quantity < quantity:
            raise InventoryError(
                f"Cannot release {quantity} of SKU '{sku}': only {item.reserved_quantity} reserved"
            )
        item.reserved_quantity -= quantity

    def deduct_stock(self, sku: str, quantity: int) -> None:
        """Deduct stock when order is fulfilled (consumes reserved stock)."""
        if quantity <= 0:
            raise ValidationError(f"Deduct quantity must be positive, got {quantity}")
        item = self.get_item(sku)
        if item.reserved_quantity < quantity:
            raise InventoryError(
                f"Cannot deduct {quantity} of SKU '{sku}': only {item.reserved_quantity} reserved"
            )
        item.reserved_quantity -= quantity
        item.stock_quantity -= quantity

    def restock(self, sku: str, quantity: int) -> None:
        """Add newly received units to warehouse stock."""
        if quantity <= 0:
            raise ValidationError(f"Restock quantity must be positive, got {quantity}")
        item = self.get_item(sku)
        item.stock_quantity += quantity

    def batch_reserve(self, items: list[tuple[str, int]]) -> None:
        """Reserve multiple items atomically. Rolls back if any reservation fails."""
        reserved_so_far: list[tuple[str, int]] = []
        try:
            for sku, qty in items:
                self.reserve_stock(sku, qty)
                reserved_so_far.append((sku, qty))
        except Exception:
            for sku, qty in reversed(reserved_so_far):
                self.release_stock(sku, qty)
            raise

    def get_low_stock_items(self, threshold: int | None = None) -> list[InventoryItem]:
        """Identify items that have reached or dropped below their reorder threshold."""
        low_items: list[InventoryItem] = []
        for item in self._items.values():
            limit = threshold if threshold is not None else item.reorder_threshold
            if item.available_quantity <= limit:
                low_items.append(item)
        return low_items
