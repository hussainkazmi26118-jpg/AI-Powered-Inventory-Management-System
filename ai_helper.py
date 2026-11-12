"""Optional Groq-powered inventory intelligence."""
import os
from typing import Any, Dict, List


class InventoryAI:
    """Wraps Groq chat completions; core inventory does not depend on this class."""

    def __init__(self) -> None:
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _complete(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError(
                "Groq is not configured. Add GROQ_API_KEY to your .env file to enable AI features."
            )
        try:
            from groq import Groq
            client = Groq(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
                max_tokens=1200,
            )
            return response.choices[0].message.content.strip()
        except ImportError as exc:
            raise RuntimeError("Groq package is not installed. Run pip install -r requirements.txt.") from exc
        except Exception as exc:
            # Do not expose secrets or provider internals to the browser.
            raise RuntimeError(f"AI service is temporarily unavailable: {type(exc).__name__}.") from exc

    @staticmethod
    def _inventory_context(products: List[Dict[str, Any]]) -> str:
        if not products:
            return "The inventory is currently empty."
        lines = []
        for p in products:
            lines.append(
                f"- {p['name']} (ID {p['product_id']}), category {p['category']}, "
                f"price {p['price']}, quantity {p['quantity']}, reorder level "
                f"{p['reorder_level']}, status {p['stock_status']}, "
                f"expiry {p.get('expiry_date') or 'not applicable'}"
            )
        return "\n".join(lines)

    def analyze_inventory(self, products: List[Dict[str, Any]], stats: dict) -> str:
        prompt = (
            f"Inventory records:\n{self._inventory_context(products)}\n\n"
            f"Summary statistics: {stats}\n\n"
            "Give a concise business-focused analysis with: overall health, urgent risks, "
            "patterns worth checking, and 3 prioritized actions. Use only the supplied data; "
            "clearly label any assumptions."
        )
        return self._complete(
            "You are a practical inventory analyst. Be accurate, concise, and never invent data.",
            prompt,
        )

    def reorder_suggestions(self, products: List[Dict[str, Any]]) -> str:
        prompt = (
            f"Inventory records:\n{self._inventory_context(products)}\n\n"
            "Identify low-stock and out-of-stock items. Suggest a practical reorder quantity "
            "for each, using the reorder level as the minimum target and explaining the "
            "assumption. Do not claim to know sales velocity or lead time because they were "
            "not supplied. Return a clear prioritized list."
        )
        return self._complete(
            "You are an inventory replenishment assistant. Do not invent sales or supplier data.",
            prompt,
        )

    def ask(self, question: str, products: List[Dict[str, Any]], stats: dict) -> str:
        prompt = (
            f"Inventory records:\n{self._inventory_context(products)}\n\n"
            f"Statistics: {stats}\n\nQuestion: {question}\n\n"
            "Answer using only this inventory. If the data does not contain the answer, say so."
        )
        return self._complete(
            "You are a helpful inventory assistant. Be direct, grounded in the provided data, "
            "and explain calculations briefly.",
            prompt,
        )

    def generate_description(self, name: str, category: str, details: str = "") -> str:
        prompt = (
            f"Product name: {name}\nCategory: {category}\nExtra details: {details or 'None'}\n\n"
            "Write a polished, factual product description of 2-3 sentences. Do not invent "
            "technical specifications, certifications, ingredients, or guarantees."
        )
        return self._complete(
            "You write clear, professional ecommerce and inventory product descriptions.",
            prompt,
        )
