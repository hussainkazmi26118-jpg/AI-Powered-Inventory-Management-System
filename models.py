"""Domain models for the inventory application."""
from datetime import date
from typing import Any, Dict, Optional


class Product:
    """A standard inventory product."""

    def __init__(
        self,
        product_id: str,
        name: str,
        category: str,
        price: float,
        quantity: int,
        reorder_level: int = 5,
        description: str = "",
    ) -> None:
        self.product_id = str(product_id)
        self.name = str(name).strip()
        self.category = str(category).strip()
        self.price = float(price)
        self.quantity = int(quantity)
        self.reorder_level = int(reorder_level)
        self.description = str(description).strip()

    def total_value(self) -> float:
        """Return the current value of this product's stock."""
        return round(self.price * self.quantity, 2)

    def stock_status(self) -> str:
        """Return a human-readable stock status."""
        if self.quantity <= 0:
            return "out_of_stock"
        if self.quantity <= self.reorder_level:
            return "low_stock"
        return "in_stock"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "quantity": self.quantity,
            "reorder_level": self.reorder_level,
            "description": self.description,
            "total_value": self.total_value(),
            "stock_status": self.stock_status(),
            "product_type": "standard",
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Product":
        if data.get("product_type") == "perishable" or data.get("expiry_date"):
            return PerishableProduct(
                product_id=data["product_id"],
                name=data["name"],
                category=data["category"],
                price=data["price"],
                quantity=data["quantity"],
                reorder_level=data.get("reorder_level", 5),
                description=data.get("description", ""),
                expiry_date=data.get("expiry_date", ""),
            )
        return cls(
            product_id=data["product_id"],
            name=data["name"],
            category=data["category"],
            price=data["price"],
            quantity=data["quantity"],
            reorder_level=data.get("reorder_level", 5),
            description=data.get("description", ""),
        )


class PerishableProduct(Product):
    """A product with an expiry date."""

    def __init__(
        self,
        product_id: str,
        name: str,
        category: str,
        price: float,
        quantity: int,
        reorder_level: int = 5,
        description: str = "",
        expiry_date: str = "",
    ) -> None:
        super().__init__(
            product_id, name, category, price, quantity, reorder_level, description
        )
        self.expiry_date = str(expiry_date).strip()

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["product_type"] = "perishable"
        data["expiry_date"] = self.expiry_date
        return data
