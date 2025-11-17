from __future__ import annotations
from typing import Any
from flask import jsonify, request
from sqlalchemy.exc import IntegrityError
from app import db
from app.api import bp
from app.models import InventoryLevel, InventoryTransaction, Product, Supplier, Warehouse

class APIError(Exception):
    status_code = 400
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
    def to_response(self):
        return jsonify({"error": self.message}), self.status_code

@bp.app_errorhandler(APIError)
def handle_api_error(error: APIError):
    return error.to_response()

@bp.app_errorhandler(IntegrityError)
def handle_integrity_error(error: IntegrityError):
    db.session.rollback()
    return jsonify({"error": "Request violates a database constraint.", "details": str(error.orig)}), 400

@bp.get("/health")
def healthcheck():
    return jsonify({"status": "ok"})

def _warehouse_to_dict(w: Warehouse) -> dict[str, Any]:
    return {
        "id": w.id,
        "name": w.name,
        "location": w.location,
        "contact_email": w.contact_email,
        "created_at": w.created_at.isoformat() if getattr(w, "created_at", None) else None,
        "updated_at": w.updated_at.isoformat() if getattr(w, "updated_at", None) else None,
    }

def _product_to_dict(p: Product) -> dict[str, Any]:
    return {
        "id": p.id,
        "sku": p.sku,
        "name": p.name,
        "description": p.description,
        "unit_price": p.unit_price,
        "unit_of_measure": p.unit_of_measure,
        "supplier": p.supplier.name if p.supplier else None,
    }

def _inventory_to_dict(lv: InventoryLevel) -> dict[str, Any]:
    return {
        "warehouse_id": lv.warehouse_id,
        "product_id": lv.product_id,
        "product_sku": lv.product.sku,
        "quantity": lv.quantity,
        "reorder_threshold": lv.reorder_threshold,
        "is_below_threshold": lv.is_below_threshold(),
    }

def _tx_to_dict(tx: InventoryTransaction) -> dict[str, Any]:
    return {
        "id": tx.id,
        "warehouse_id": tx.warehouse_id,
        "product_id": tx.product_id,
        "quantity_delta": tx.quantity_delta,
        "resulting_quantity": tx.resulting_quantity,
        "reason": tx.reason,
        "created_at": tx.created_at.isoformat() if tx.created_at else None,
    }

# Warehouses
@bp.get("/warehouses")
def list_warehouses():
    ws = Warehouse.query.order_by(Warehouse.name).all()
    return jsonify([_warehouse_to_dict(w) for w in ws])

@bp.post("/warehouses")
def create_warehouse():
    data = request.get_json() or {}
    if "name" not in data:
        raise APIError("'name' is a required field.")
    w = Warehouse(name=data["name"], location=data.get("location"), contact_email=data.get("contact_email"))
    db.session.add(w)
    db.session.commit()
    return jsonify(_warehouse_to_dict(w)), 201

# Products
@bp.get("/products")
def list_products():
    ps = Product.query.order_by(Product.name).all()
    return jsonify([_product_to_dict(p) for p in ps])

@bp.post("/products")
def create_product():
    data = request.get_json() or {}
    for field in ["sku", "name"]:
        if field not in data:
            raise APIError(f"'{field}' is a required field.")
    supplier = None
    if data.get("supplier"):
        supplier = Supplier.query.filter_by(name=data["supplier"]).first()
        if supplier is None:
            supplier = Supplier(name=data["supplier"])
            db.session.add(supplier)
    p = Product(
        sku=data["sku"], name=data["name"], description=data.get("description"),
        unit_price=data.get("unit_price"), unit_of_measure=data.get("unit_of_measure"), supplier=supplier
    )
    db.session.add(p)
    db.session.commit()
    return jsonify(_product_to_dict(p)), 201

@bp.patch("/products/<int:product_id>")
def update_product(product_id: int):
    p = Product.query.get_or_404(product_id)
    data = request.get_json() or {}
    for field in ["sku", "name", "description", "unit_price", "unit_of_measure"]:
        if field in data:
            setattr(p, field, data[field])
    if "supplier" in data:
        name = data.get("supplier")
        if name:
            s = Supplier.query.filter_by(name=name).first() or Supplier(name=name)
            db.session.add(s)
            p.supplier = s
        else:
            p.supplier = None
    db.session.commit()
    return jsonify(_product_to_dict(p))

@bp.delete("/products/<int:product_id>")
def delete_product(product_id: int):
    p = Product.query.get_or_404(product_id)
    db.session.delete(p)
    db.session.commit()
    return "", 204

# Inventory views
@bp.get("/warehouses/<int:warehouse_id>/inventory")
def list_inventory(warehouse_id: int):
    w = Warehouse.query.get_or_404(warehouse_id)
    levels = (InventoryLevel.query.filter_by(warehouse_id=w.id).join(Product).order_by(Product.name).all())
    return jsonify({
        "warehouse": _warehouse_to_dict(w),
        "inventory": [_inventory_to_dict(lv) for lv in levels],
    })

@bp.post("/inventory/adjust")
def adjust_inventory():
    data = request.get_json() or {}
    warehouse_id = data.get("warehouse_id")
    product_id = data.get("product_id")
    delta = data.get("quantity_delta")
    if None in (warehouse_id, product_id, delta):
        raise APIError("'warehouse_id', 'product_id', and 'quantity_delta' are required fields.")
    level = InventoryLevel.query.filter_by(warehouse_id=warehouse_id, product_id=product_id).first()
    if level is None:
        w = Warehouse.query.get_or_404(warehouse_id)
        p = Product.query.get_or_404(product_id)
        level = InventoryLevel(warehouse=w, product=p, quantity=0)
        db.session.add(level)
    tx = level.apply_delta(int(delta), data.get("reason"))
    db.session.commit()
    return jsonify({"inventory": _inventory_to_dict(level), "transaction": _tx_to_dict(tx)})

@bp.get("/transactions")
def list_transactions():
    txs = InventoryTransaction.query.order_by(InventoryTransaction.created_at.desc()).limit(100).all()
    return jsonify([_tx_to_dict(tx) for tx in txs])
