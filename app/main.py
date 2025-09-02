from fastapi import FastAPI

from app.routers import customers
from app.routers import catagory
from app.routers import products
from app.routers import orders

app = FastAPI(
    title="Ecom API",
    description="Ecom",
    version="v1"
)

app.include_router(customers.router)
app.include_router(catagory.router)
app.include_router(products.router)
app.include_router(orders.router)