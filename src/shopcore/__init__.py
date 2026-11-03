"""ShopCore: Core e-commerce business-logic library."""

from shopcore.exceptions import (
    InsufficientStockError,
    InvalidDiscountError,
    InvalidOrderStateError,
    InventoryError,
    ItemNotFoundError,
    OrderError,
    PricingError,
    ShopCoreError,
    UserNotFoundError,
    ValidationError,
)
from shopcore.inventory import InventoryItem, InventoryManager
from shopcore.orders import Order, OrderItem, OrderService, OrderStatus
from shopcore.pricing import (
    apply_bulk_discount,
    calculate_item_subtotal,
    calculate_order_totals,
    calculate_shipping,
    calculate_tax,
)
from shopcore.users import User, UserManager, UserTier

__version__ = "0.1.0"

__all__ = [
    "InsufficientStockError",
    "InvalidDiscountError",
    "InvalidOrderStateError",
    "InventoryError",
    "InventoryItem",
    "InventoryManager",
    "ItemNotFoundError",
    "Order",
    "OrderError",
    "OrderItem",
    "OrderService",
    "OrderStatus",
    "PricingError",
    "ShopCoreError",
    "User",
    "UserManager",
    "UserNotFoundError",
    "UserTier",
    "ValidationError",
    "apply_bulk_discount",
    "calculate_item_subtotal",
    "calculate_order_totals",
    "calculate_shipping",
    "calculate_tax",
]

