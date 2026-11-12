"""JSON-backed inventory repository and business logic."""
import json
import os
import threading
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from models import Product, PerishableProduct


class InventoryManager:
    """Manages products and persists them to a JSON file."""

    def __init__(self, data_file: Optional[str] = None) -> None:
        default_file = Path(__file__).resolve().parent / "data" / "products.json"
        self.data_file = Path(data_file or os.getenv("INVENTORY_DATA_FILE", default_file))
        self._lock = threading.RLock()
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.products: Dict[str, Product] = {}
        self.load_products()

    def load_products(self) -> None:
        with self._lock:
            if not self.data_file.exists():
                self.products = {}
                self.save_products()
                return
            try:
                raw = json.loads(self.data_file.read_text(encoding="utf-8") or "[]")
                self.products = {
                    str(item["product_id"]): Product.from_dict(item)
                    for item in raw
                }
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                raise RuntimeError(f"Could not read inventory data: {exc}") from exc

    def save_products(self) -> None:
        with self._lock:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            temp_file = self.data_file.with_suffix(self.data_file.suffix + ".tmp")
            payload = [product.to_dict() for product in self.products.values()]
            temp_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            temp_file.replace(self.data_file)

    def add_product(self, data: dict) -> Product:
        with self._lock:
            product_id = str(data.get("product_id") or uuid4().hex[:8].upper())
            if product_id in self.products:
                raise ValueError("A product with this ID already exists.")
            product = self._build_product(product_id, data)
            self.products[product_id] = product
            self.save_products()
            return product

    def update_product(self, product_id: str, data: dict) -> Product:
        with self._lock:
            if product_id not in self.products:
                raise KeyError("Product not found.")
            merged = self.products[product_id].to_dict()
            merged.update(data)
            merged["product_id"] = product_id
            product = self._build_product(product_id, merged)
            self.products[product_id] = product
            self.save_products()
            return product

    def delete_product(self, product_id: str) -> None:
        with self._lock:
            if product_id not in self.products:
                raise KeyError("Product not found.")
            del self.products[product_id]
            self.save_products()

    def get_product(self, product_id: str) -> Optional[Product]:
        return self.products.get(str(product_id))

    def get_all_products(self) -> List[Product]:
        return sorted(self.products.values(), key=lambda p: p.name.lower())

    def search_products(self, query: str) -> List[Product]:
        query = query.strip().lower()
        if not query:
            return self.get_all_products()
        return [
            p for p in self.get_all_products()
            if query in p.name.lower()
            or query in p.product_id.lower()
            or query in p.category.lower()
        ]

    def low_stock_products(self) -> List[Product]:
        return [p for p in self.get_all_products() if p.stock_status() == "low_stock"]

    def out_of_stock_products(self) -> List[Product]:
        return [p for p in self.get_all_products() if p.stock_status() == "out_of_stock"]

    def statistics(self) -> dict:
        products = self.get_all_products()
        return {
            "total_products": len(products),
            "total_units": sum(p.quantity for p in products),
            "inventory_value": round(sum(p.total_value() for p in products), 2),
            "low_stock_count": len(self.low_stock_products()),
            "out_of_stock_count": len(self.out_of_stock_products()),
        }

    @staticmethod
    def _build_product(product_id: str, data: dict) -> Product:
        common = dict(
            product_id=product_id,
            name=data["name"],
            category=data["category"],
            price=data["price"],
            quantity=data["quantity"],
            reorder_level=data.get("reorder_level", 5),
            description=data.get("description", ""),
        )
        if data.get("product_type") == "perishable" or data.get("expiry_date"):
            return PerishableProduct(**common, expiry_date=data.get("expiry_date", ""))
        return Product(**common)
