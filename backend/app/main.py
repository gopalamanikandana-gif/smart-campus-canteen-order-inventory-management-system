from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .database import Base, engine
from .api import auth, menu, orders

settings = get_settings()
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Campus Canteen API",
    version="1.0.0",
    description="Secure order and inventory management API for the internship assessment.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(menu.router)
app.include_router(orders.router)


@app.get("/health")
def health():
    return {"status": "ok"}
