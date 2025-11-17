from __future__ import annotations
from datetime import datetime
from sqlalchemy import UniqueConstraint, event
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app import db

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class Warehouse(db.Model, TimestampMixin):
    __tablename__ = "warehouses"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    location: Mapped[str | None]
    contact_email: Mapped[str | None]
    inventory_levels: Mapped[list["InventoryLevel"]] = relationship("InventoryLevel", back_populates="warehouse", cascade="all, delete-orphan")
    transactions: Mapped[list["InventoryTransaction"]] = relationship("InventoryTransaction", back_populates="warehouse")
    def __repr__(self) -> str:
        return f"<Warehouse {self.name!r}>"

class Supplier(db.Model, TimestampMixin):
    __tablename__ = "suppliers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    contact_name: Mapped[str | None]
    phone: Mapped[str | None]
    email: Mapped[str | None]
    products: Mapped[list["Product"]] = relationship("Product", back_populates="supplier")
    def __repr__(self) -> str:
        return f"<Supplier {self.name!r}>"

class Product(db.Model, TimestampMixin):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(unique=True, nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None]
    unit_price: Mapped[float | None]
    unit_of_measure: Mapped[str | None]
    supplier_id: Mapped[int | None] = mapped_column(db.ForeignKey("suppliers.id"))
    supplier: Mapped[Supplier | None] = relationship("Supplier", back_populates="products")
    inventory_levels: Mapped[list["InventoryLevel"]] = relationship("InventoryLevel", back_populates="product", cascade="all, delete-orphan")
    transactions: Mapped[list["InventoryTransaction"]] = relationship("InventoryTransaction", back_populates="product")
    def __repr__(self) -> str:
        return f"<Product {self.sku!r}>"

class InventoryLevel(db.Model, TimestampMixin):
    __tablename__ = "inventory_levels"
    __table_args__ = (UniqueConstraint("warehouse_id", "product_id", name="uix_inventory_level"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    warehouse_id: Mapped[int] = mapped_column(db.ForeignKey("warehouses.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(db.ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(default=0, nullable=False)
    reorder_threshold: Mapped[int] = mapped_column(default=0, nullable=False)
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="inventory_levels")
    product: Mapped["Product"] = relationship("Product", back_populates="inventory_levels")

    def apply_delta(self, delta: int, reason: str | None = None) -> "InventoryTransaction":
        self.quantity += delta
        tx = InventoryTransaction(warehouse=self.warehouse, product=self.product, quantity_delta=delta, resulting_quantity=self.quantity, reason=reason or "manual_adjustment")
        db.session.add(tx)
        return tx

    def is_below_threshold(self) -> bool:
        return self.quantity < self.reorder_threshold

    def __repr__(self) -> str:
        return f"<InventoryLevel {self.warehouse_id=} {self.product_id=} {self.quantity=}>"

class InventoryTransaction(db.Model):
    __tablename__ = "inventory_transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    warehouse_id: Mapped[int] = mapped_column(db.ForeignKey("warehouses.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(db.ForeignKey("products.id"), nullable=False)
    quantity_delta: Mapped[int] = mapped_column(nullable=False)
    resulting_quantity: Mapped[int] = mapped_column(nullable=False)
    reason: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="transactions")
    product: Mapped["Product"] = relationship("Product", back_populates="transactions")
    def __repr__(self) -> str:
        return f"<InventoryTransaction {self.id} delta={self.quantity_delta}>"

@event.listens_for(InventoryLevel, "before_insert")
def set_initial_quantity(mapper, connection, target):
    if target.quantity is None:
        target.quantity = 0

@event.listens_for(InventoryLevel, "before_update")
def ensure_quantity_not_negative(mapper, connection, target):
    if target.quantity < 0:
        raise ValueError("Inventory quantity cannot be negative")
