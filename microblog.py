from app import create_app, db
from app.models import Warehouse, Product, InventoryLevel, InventoryTransaction, Supplier

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "Warehouse": Warehouse,
        "Product": Product,
        "InventoryLevel": InventoryLevel,
        "InventoryTransaction": InventoryTransaction,
        "Supplier": Supplier,
    }
