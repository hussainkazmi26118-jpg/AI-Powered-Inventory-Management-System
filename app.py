"""Flask entry point and JSON API."""
import os
from datetime import date
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from ai_helper import InventoryAI
from inventory import InventoryManager

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024
inventory = InventoryManager()
inventory_ai = InventoryAI()


def api_error(message: str, status: int = 400):
    return jsonify({"success": False, "error": message}), status


def validate_product_payload(data, partial=False):
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")
    required = ["name", "category", "price", "quantity"]
    if not partial:
        missing = [field for field in required if field not in data or str(data[field]).strip() == ""]
        if missing:
            raise ValueError("Required fields are missing: " + ", ".join(missing))
    result = dict(data)
    for field in ("name", "category"):
        if field in result:
            value = str(result[field]).strip()
            if not value or len(value) > 100:
                raise ValueError(f"{field.title()} must be between 1 and 100 characters.")
            result[field] = value
    if "description" in result and len(str(result["description"])) > 1000:
        raise ValueError("Description must be 1000 characters or fewer.")
    if "price" in result:
        try:
            result["price"] = float(result["price"])
        except (TypeError, ValueError):
            raise ValueError("Price must be a valid number.")
        if result["price"] < 0 or result["price"] > 1000000000:
            raise ValueError("Price must be between 0 and 1,000,000,000.")
    for field in ("quantity", "reorder_level"):
        if field in result:
            try:
                number = int(result[field])
            except (TypeError, ValueError):
                raise ValueError(f"{field.replace('_', ' ').title()} must be a whole number.")
            if number < 0 or number > 1000000000:
                raise ValueError(f"{field.replace('_', ' ').title()} cannot be negative.")
            result[field] = number
    if "product_type" in result and result["product_type"] not in ("standard", "perishable"):
        raise ValueError("Product type must be standard or perishable.")
    if result.get("product_type") == "perishable" or result.get("expiry_date"):
        result["product_type"] = "perishable"
        expiry = str(result.get("expiry_date", "")).strip()
        if not expiry:
            raise ValueError("Expiry date is required for perishable products.")
        try:
            date.fromisoformat(expiry)
        except ValueError:
            raise ValueError("Expiry date must be a valid date.")
        result["expiry_date"] = expiry
    return result


@app.get("/")
def home():
    return render_template("index.html", ai_available=inventory_ai.available)


@app.get("/api/products")
def get_products():
    query = request.args.get("q", "")
    products = [p.to_dict() for p in inventory.search_products(query)]
    return jsonify({"success": True, "products": products})


@app.post("/api/products")
def create_product():
    try:
        data = validate_product_payload(request.get_json(silent=True) or {})
        product = inventory.add_product(data)
        return jsonify({"success": True, "product": product.to_dict(), "message": "Product added."}), 201
    except ValueError as exc:
        return api_error(str(exc))
    except Exception:
        app.logger.exception("Could not add product")
        return api_error("Could not save the product.", 500)


@app.put("/api/products/<product_id>")
def update_product(product_id):
    try:
        data = validate_product_payload(request.get_json(silent=True) or {}, partial=True)
        product = inventory.update_product(product_id, data)
        return jsonify({"success": True, "product": product.to_dict(), "message": "Product updated."})
    except KeyError as exc:
        return api_error(str(exc).strip("'"), 404)
    except ValueError as exc:
        return api_error(str(exc))
    except Exception:
        app.logger.exception("Could not update product")
        return api_error("Could not update the product.", 500)


@app.delete("/api/products/<product_id>")
def delete_product(product_id):
    try:
        inventory.delete_product(product_id)
        return jsonify({"success": True, "message": "Product deleted."})
    except KeyError:
        return api_error("Product not found.", 404)
    except Exception:
        app.logger.exception("Could not delete product")
        return api_error("Could not delete the product.", 500)


@app.get("/api/stats")
def get_stats():
    return jsonify({"success": True, "stats": inventory.statistics()})


def ai_guard(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not inventory_ai.available:
            return api_error("AI is not configured. Add GROQ_API_KEY to your .env file; normal inventory features still work.", 503)
        try:
            return jsonify({"success": True, "answer": func(*args, **kwargs)})
        except RuntimeError as exc:
            return api_error(str(exc), 503)
        except Exception:
            app.logger.exception("AI request failed")
            return api_error("The AI request could not be completed.", 503)
    return wrapper


@app.post("/api/ai/analyze")
@ai_guard
def ai_analyze():
    products = [p.to_dict() for p in inventory.get_all_products()]
    return inventory_ai.analyze_inventory(products, inventory.statistics())


@app.post("/api/ai/reorder")
@ai_guard
def ai_reorder():
    products = [p.to_dict() for p in inventory.get_all_products()]
    return inventory_ai.reorder_suggestions(products)


@app.post("/api/ai/ask")
@ai_guard
def ai_ask():
    data = request.get_json(silent=True) or {}
    question = str(data.get("question", "")).strip()
    if not question or len(question) > 500:
        raise ValueError("Please enter a question of 1 to 500 characters.")
    products = [p.to_dict() for p in inventory.get_all_products()]
    return inventory_ai.ask(question, products, inventory.statistics())


@app.post("/api/ai/description")
@ai_guard
def ai_description():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    category = str(data.get("category", "")).strip()
    details = str(data.get("details", "")).strip()
    if not name or not category:
        raise ValueError("Product name and category are required to generate a description.")
    if len(name) > 100 or len(category) > 100 or len(details) > 500:
        raise ValueError("Please keep product details within the allowed length.")
    return inventory_ai.generate_description(name, category, details)


@app.errorhandler(413)
def too_large(_error):
    return api_error("Request is too large.", 413)


@app.errorhandler(404)
def not_found(_error):
    if request.path.startswith("/api/"):
        return api_error("API endpoint not found.", 404)
    return "Page not found", 404


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")
