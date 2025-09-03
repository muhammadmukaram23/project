from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import customers
from app.routers import catagory
from app.routers import products
from app.routers import orders

app = FastAPI(
    title="Ecom API",
    description="Ecom",
    version="v1"
)

# ✅ Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Routers
app.include_router(customers.router)
app.include_router(catagory.router)
app.include_router(products.router)
app.include_router(orders.router)
