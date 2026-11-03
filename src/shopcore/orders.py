"""Order processing, lifecycle management, and checkout operations."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from shopcore.exceptions import (
    InvalidOrderStateError,
    OrderError,
    ValidationError,
)
from shopcore.inventory import InventoryManager
from shopcore.pricing import (
    apply_bulk_discount,
    calculate_order_totals,
    calculate_shipping,
)
from shopcore.users import UserManager


class OrderStatus(str, Enum):
    """Lifecycle status of an order."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


@dataclass
class OrderItem:
    """Individual line item within an order."""

    sku: str
    quantity: int
    unit_price: Decimal


@dataclass
class Order:
    """Represents a customer purchase order."""

    order_id: str
    user_id: str
    items: list[OrderItem]
    status: OrderStatus
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    shipping: Decimal
    total: Decimal
    points_awarded: int = 0


class OrderService:
    """Coordinates inventory, pricing, user accounts, and order lifecycle."""

    def __init__(self, inventory: InventoryManager, users: UserManager) -> None:
        self.inventory = inventory
        self.users = users
        self._orders: dict[str, Order] = {}

    def get_order(self, order_id: str) -> Order:
        """Fetch an order by its unique ID."""
        if order_id not in self._orders:
            raise OrderError(f"Order '{order_id}' not found")
        return self._orders[order_id]

    def create_order(
        self,
        order_id: str,
        user_id: str,
        items: list[OrderItem],
        weight_kg: Decimal = Decimal("1.0"),
    ) -> Order:
        """Create a new pending order and reserve inventory."""
        if not order_id or not order_id.strip():
            raise ValidationError("Order ID cannot be empty")
        if order_id in self._orders:
            raise OrderError(f"Order '{order_id}' already exists")
        if not items:
            raise ValidationError("Order must contain at least one item")

        user = self.users.get_user(user_id)
        if not user.is_active:
            raise ValidationError(f"User '{user_id}' is inactive")

        # Validate item availability and pricing
        total_items_count = 0
        items_subtotal = Decimal("0.00")
        reservation_requests: list[tuple[str, int]] = []

        for item in items:
            if item.quantity <= 0:
                raise ValidationError(f"Item quantity must be positive: {item.sku}")
            inv_item = self.inventory.get_item(item.sku)
            if item.unit_price != inv_item.unit_price:
                msg = (
                    f"Unit price mismatch for SKU '{item.sku}': "
                    f"expected {inv_item.unit_price}, got {item.unit_price}"
                )
                raise ValidationError(msg)
            items_subtotal += item.unit_price * Decimal(item.quantity)
            total_items_count += item.quantity
            reservation_requests.append((item.sku, item.quantity))

        # Atomic reservation
        self.inventory.batch_reserve(reservation_requests)

        # Calculate pricing
        bulk_discount = apply_bulk_discount(items_subtotal, total_items_count)
        shipping_fee = calculate_shipping(weight_kg)
        financials = calculate_order_totals(
            items_subtotal=items_subtotal,
            discount_amount=bulk_discount,
            shipping_fee=shipping_fee,
        )

        order = Order(
            order_id=order_id.strip(),
            user_id=user_id,
            items=items,
            status=OrderStatus.PENDING,
            subtotal=financials["subtotal"],
            discount=financials["discount"],
            tax=financials["tax"],
            shipping=financials["shipping"],
            total=financials["total"],
        )
        self._orders[order.order_id] = order
        return order

    def confirm_order(self, order_id: str) -> Order:
        """Confirm payment and deduct inventory."""
        order = self.get_order(order_id)
        if order.status != OrderStatus.PENDING:
            raise InvalidOrderStateError(
                f"Cannot confirm order in status '{order.status.value}'"
            )

        # Deduct stock for all items
        for item in order.items:
            self.inventory.deduct_stock(item.sku, item.quantity)

        # 1 loyalty point per 10 dollars of order total
        points = int(order.total // Decimal("10.00"))
        if points > 0:
            self.users.add_loyalty_points(order.user_id, points)
            order.points_awarded = points

        order.status = OrderStatus.CONFIRMED
        return order

    def cancel_order(self, order_id: str) -> Order:
        """Cancel an order and return inventory based on lifecycle status."""
        order = self.get_order(order_id)
        if order.status == OrderStatus.CANCELLED:
            raise InvalidOrderStateError("Order is already cancelled")

        if order.status == OrderStatus.PENDING:
            # Release pending reservations
            for item in order.items:
                self.inventory.release_stock(item.sku, item.quantity)
        elif order.status == OrderStatus.CONFIRMED:
            # Restock deducted inventory
            for item in order.items:
                self.inventory.restock(item.sku, item.quantity)
            if order.points_awarded > 0:
                self.users.deduct_loyalty_points(order.user_id, order.points_awarded)

        order.status = OrderStatus.CANCELLED
        return order
