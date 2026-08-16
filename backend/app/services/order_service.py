from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from ..config import get_settings
from ..models import MenuItem, Order, OrderItem, User
from ..schemas import OrderCreate


def is_canteen_open(now: datetime | None = None) -> bool:
    settings = get_settings()
    current = now or datetime.now()
    return settings.canteen_open_hour <= current.hour < settings.canteen_close_hour


def create_order(db: Session, user: User, request: OrderCreate) -> Order:
    settings = get_settings()

    if not is_canteen_open():
        raise HTTPException(status_code=400, detail="Canteen is closed")

    if not request.items:
        raise HTTPException(status_code=400, detail="Cart cannot be empty")

    seen = set()
    menu_ids = []
    for line in request.items:
        if line.menu_item_id in seen:
            raise HTTPException(status_code=400, detail="Duplicate menu item in order")
        seen.add(line.menu_item_id)
        if line.quantity > settings.max_item_quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum quantity per item is {settings.max_item_quantity}",
            )
        menu_ids.append(line.menu_item_id)

    menu_items = db.query(MenuItem).filter(MenuItem.id.in_(menu_ids)).all()
    by_id = {item.id: item for item in menu_items}

    if len(by_id) != len(menu_ids):
        raise HTTPException(status_code=404, detail="One or more menu items not found")

    order_lines = []
    total = 0.0

    for line in request.items:
        item = by_id[line.menu_item_id]

        if not item.is_available:
            raise HTTPException(status_code=400, detail=f"{item.name} is unavailable")

        if item.stock < line.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {item.name}")

        # Price is deliberately read from the database, never trusted from the client.
        subtotal = item.price * line.quantity
        total += subtotal

        item.stock -= line.quantity
        order_lines.append(
            OrderItem(
                menu_item_id=item.id,
                quantity=line.quantity,
                unit_price=item.price,
                subtotal=subtotal,
            )
        )

    order = Order(user_id=user.id, total_amount=round(total, 2), status="PENDING")
    db.add(order)
    db.flush()

    for line in order_lines:
        line.order_id = order.id
        db.add(line)

    db.commit()
    db.refresh(order)
    return order
