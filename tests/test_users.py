"""Tests for user account management and loyalty tier progression."""

import pytest

from shopcore.exceptions import ValidationError
from shopcore.users import UserManager, UserTier, calculate_tier, validate_email


def test_validate_email_formats() -> None:
    assert validate_email("user@example.com") is True
    assert validate_email("first.last@sub.domain.co") is True
    assert validate_email("invalid-email") is False
    assert validate_email("") is False


def test_calculate_tier_thresholds() -> None:
    assert calculate_tier(0) == UserTier.STANDARD
    assert calculate_tier(99) == UserTier.STANDARD
    assert calculate_tier(100) == UserTier.SILVER
    assert calculate_tier(499) == UserTier.SILVER
    assert calculate_tier(500) == UserTier.GOLD
    assert calculate_tier(999) == UserTier.GOLD
    assert calculate_tier(1000) == UserTier.PLATINUM
    assert calculate_tier(2500) == UserTier.PLATINUM


def test_register_user_success() -> None:
    manager = UserManager()
    user = manager.register_user("usr_001", "Alice@Example.com", "Alice Smith")
    assert user.user_id == "usr_001"
    assert user.email == "alice@example.com"
    assert user.tier == UserTier.STANDARD
    assert user.loyalty_points == 0


def test_register_user_validation_failures() -> None:
    manager = UserManager()
    with pytest.raises(ValidationError):
        manager.register_user("", "alice@example.com", "Alice")

    with pytest.raises(ValidationError):
        manager.register_user("u2", "invalid-email", "Bob")

    with pytest.raises(ValidationError):
        manager.register_user("u3", "bob@example.com", "   ")


def test_register_user_duplicate_email() -> None:
    manager = UserManager()
    manager.register_user("u1", "alice@example.com", "Alice")
    with pytest.raises(ValidationError):
        # Case insensitive duplicate check
        manager.register_user("u2", "ALICE@EXAMPLE.COM", "Alice Clone")


def test_loyalty_point_lifecycle() -> None:
    manager = UserManager()
    manager.register_user("u1", "alice@example.com", "Alice")

    # Add points to reach Silver
    pts = manager.add_loyalty_points("u1", 120)
    assert pts == 120
    assert manager.get_user("u1").tier == UserTier.SILVER

    # Deduct points
    pts_left = manager.deduct_loyalty_points("u1", 30)
    assert pts_left == 90
    assert manager.get_user("u1").tier == UserTier.STANDARD

    # Cannot deduct more than balance
    with pytest.raises(ValidationError):
        manager.deduct_loyalty_points("u1", 100)
