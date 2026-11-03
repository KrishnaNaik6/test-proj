"""Custom exception hierarchy for ShopCore."""


class ShopCoreError(Exception):
    """Base exception for all shopcore errors."""


class InventoryError(ShopCoreError):
    """Base exception for inventory-related operations."""


class InsufficientStockError(InventoryError):
    """Raised when an operation requests more stock than available."""


class ItemNotFoundError(InventoryError):
    """Raised when an inventory item SKU cannot be found."""


class PricingError(ShopCoreError):
    """Base exception for pricing and discount calculations."""


class InvalidDiscountError(PricingError):
    """Raised when a discount amount or rate is invalid."""


class ValidationError(ShopCoreError):
    """Raised when user or order input validation fails."""


class UserNotFoundError(ShopCoreError):
    """Raised when a user ID cannot be found."""


class OrderError(ShopCoreError):
    """Base exception for order management operations."""


class InvalidOrderStateError(OrderError):
    """Raised when an illegal order transition is attempted."""
