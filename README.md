# ShopCore

ShopCore is a Python library providing core business logic for e-commerce store operations, including product pricing and discount calculations, inventory allocation, order lifecycle management, and customer loyalty tiers.

## Features

- **Product Pricing & Discounts**: Tiered bulk purchase discounts, tax calculations, and weight-based shipping rates.
- **Inventory Management**: Inventory tracking, stock reservations, order fulfillment deductions, restocks, and reorder alerts.
- **User Management**: Customer registrations with email normalization, data validation, and loyalty tier advancement.
- **Order Lifecycle**: End-to-end checkout workflow spanning reservation, confirmation, and cancellation.

## Requirements

- Python 3.12+

## Installation

Clone the repository and install dependencies in editable mode:

```bash
git clone https://github.com/KrishnaNaik6/test-proj.git
cd test-proj
python -m pip install -e .[dev]
```

## Running Tests

Execute the automated test suite with `pytest`:

```bash
pytest -v
```

Linting and type checking:

```bash
ruff check .
mypy src
```

## Architecture

- `shopcore.pricing`: Pricing, discount calculations, tax quantization, and shipping fees.
- `shopcore.inventory`: Inventory items, reservations, deductions, and low-stock queries.
- `shopcore.users`: User models, tier progression (Standard, Silver, Gold, Platinum), and loyalty points.
- `shopcore.orders`: Order coordination, state transitions (`pending` -> `confirmed` / `cancelled`), and atomic inventory interactions.
