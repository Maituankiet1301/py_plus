# app/cli.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable

import click
from flask import Flask

from app import db
from app.models import InventoryLevel, Product, Supplier, Warehouse


def _load_seed_data(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _create_or_get_supplier(name: str | None) -> Supplier | None:
    if not name:
        return None
    supplier = Supplier.query.filter_by(name=name).first()
    if supplier:
        return supplier
    supplier = Supplier(name=name)
    db.session.add(supplier)
    return supplier


def _create_product(payload: dict) -> Product:
    supplier = _create_or_get_supplier(payload.get("supplier"))
    product = Product(
        sku=payload["sku"],
        name=payload["name"],
        description=payload.get("description"),
        unit_price=payload.get("unit_price"),
        unit_of_measure=payload.get("unit_of_measure"),
        supplier=supplier,
    )
    return product


def _ensure_inventory_levels(product: Product, levels: Iterable[dict]):
    for level_data in levels:
        warehouse = Warehouse.query.filter_by(name=level_data["warehouse"]).first()
        if warehouse is None:
            warehouse = Warehouse(
                name=level_data["warehouse"],
                location=level_data.get("location"),
            )
            db.session.add(warehouse)
            db.session.flush()
        level = InventoryLevel(
            warehouse=warehouse,
            product=product,
            quantity=level_data.get("quantity", 0),
            reorder_threshold=level_data.get("reorder_threshold", 0),
        )
        db.session.add(level)


def register_cli_commands(app: Flask) -> None:
    @app.cli.group()
    def translate():
        """Localization command group placeholder."""

    @translate.command()
    def compile():
        """Stub translation compilation command."""
        click.echo("No translation files to compile.")

    @translate.command()
    def update():
        click.echo("No translation files to update.")

    @app.cli.command()
    @click.argument("seed_file", type=click.Path(path_type=Path))
    def seed(seed_file: Path):
        """Load seed data into the database."""
        payload = _load_seed_data(seed_file)

        for warehouse_data in payload.get("warehouses", []):
            warehouse = Warehouse.query.filter_by(name=warehouse_data["name"]).first()
            if warehouse is None:
                warehouse = Warehouse(
                    name=warehouse_data["name"],
                    location=warehouse_data.get("location"),
                    contact_email=warehouse_data.get("contact_email"),
                )
                db.session.add(warehouse)

        db.session.flush()

        for product_data in payload.get("products", []):
            product = Product.query.filter_by(sku=product_data["sku"]).first()
            if product is None:
                product = _create_product(product_data)
                db.session.add(product)
                db.session.flush()
            _ensure_inventory_levels(product, product_data.get("inventory_levels", []))

        db.session.commit()
        click.echo("Seed data imported successfully.")
