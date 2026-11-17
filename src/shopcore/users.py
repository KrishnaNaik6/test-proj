"""User accounts, customer tiers, and loyalty management."""

import re
from dataclasses import dataclass
from enum import Enum

from shopcore.exceptions import (
    UserNotFoundError,
    ValidationError,
)

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class UserTier(str, Enum):
    """Customer loyalty status tiers."""

    STANDARD = "standard"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


@dataclass
class User:
    """Represents a registered customer account."""

    user_id: str
    email: str
    name: str
    tier: UserTier = UserTier.STANDARD
    loyalty_points: int = 0
    is_active: bool = True


def validate_email(email: str) -> bool:
    """Validate that the email address conforms to basic standard format."""
    if not email:
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def calculate_tier(loyalty_points: int) -> UserTier:
    """Determine customer tier based on accumulated loyalty points."""
    if loyalty_points < 0:
        raise ValidationError("Loyalty points cannot be negative")

    if loyalty_points >= 1000:
        return UserTier.PLATINUM
    if loyalty_points >= 500:
        return UserTier.GOLD
    if loyalty_points >= 100:
        return UserTier.SILVER
    return UserTier.STANDARD


class UserManager:
    """Handles user registrations, lookups, and loyalty point rewards."""

    def __init__(self) -> None:
        self._users_by_id: dict[str, User] = {}
        self._users_by_email: dict[str, str] = {}  # normalized email -> user_id

    def register_user(self, user_id: str, email: str, name: str) -> User:
        """Register a new customer account.

        Raises:
            ValidationError: If email is invalid, name is empty, or email already registered.
        """
        if not user_id or not user_id.strip():
            raise ValidationError("User ID cannot be empty")
        if not name:
            raise ValidationError("Name cannot be empty")
        if not validate_email(email):
            raise ValidationError(f"Invalid email address: {email}")

        normalized_email = email.strip().lower()
        if normalized_email in self._users_by_email:
            raise ValidationError(f"User with email '{email}' already registered")
        if user_id in self._users_by_id:
            raise ValidationError(f"User ID '{user_id}' already registered")

        user = User(
            user_id=user_id.strip(),
            email=normalized_email,
            name=name.strip(),
            tier=UserTier.STANDARD,
            loyalty_points=0,
            is_active=True,
        )
        self._users_by_id[user.user_id] = user
        self._users_by_email[normalized_email] = user.user_id
        return user

    def get_user(self, user_id: str) -> User:
        """Retrieve user by ID."""
        if user_id not in self._users_by_id:
            raise UserNotFoundError(f"User with ID '{user_id}' not found")
        return self._users_by_id[user_id]

    def add_loyalty_points(self, user_id: str, points: int) -> int:
        """Award loyalty points to a user and update tier if threshold reached."""
        if points <= 0:
            raise ValidationError(f"Points to add must be positive, got {points}")
        user = self.get_user(user_id)
        user.loyalty_points += points
        user.tier = calculate_tier(user.loyalty_points)
        return user.loyalty_points

    def deduct_loyalty_points(self, user_id: str, points: int) -> int:
        """Deduct loyalty points from a user account for redemptions or adjustments."""
        if points <= 0:
            raise ValidationError(f"Points to deduct must be positive, got {points}")
        user = self.get_user(user_id)
        if user.loyalty_points < points:
            raise ValidationError(
                f"Cannot deduct {points} points: user only has {user.loyalty_points} points"
            )
        user.loyalty_points -= points
        user.tier = calculate_tier(user.loyalty_points)
        return user.loyalty_points
