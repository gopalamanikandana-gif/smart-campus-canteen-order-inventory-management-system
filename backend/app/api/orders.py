from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from ..auth import get_current_user, require_admin
from ..database import get_db
from ..models import Order, OrderItem, User
from ..schemas import OrderCreate, OrderResponse, OrderItemResponse, StatusUpdate
from ..services.order_service import create_order

router = APIRouter(prefix="/orders", tags=["orders"])


def serialize_order(order: Order) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        total_amount=order.total_amount,
        status=order.status,
        created_at=order.created_at,
        items=[
            OrderItemResponse(
                menu_item_id=x.menu_item_id,
                name=x.menu_item.name,
                quantity=x.quantity,
                unit_price=x.unit_price,
                subtotal=x.subtotal,
            )
            for x in order.items
        ],
    )


@router.post("", response_model=OrderResponse, status_code=201)
def place_order(
    request: OrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = create_order(db, user, request)
    order = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.menu_item))
        .filter(Order.id == order.id)
        .first()
    )
    return serialize_order(order)


@router.get("", response_model=list[OrderResponse])
def my_orders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    orders = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.menu_item))
        .filter(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return [serialize_order(o) for o in orders]


@router.get("/admin/all", response_model=list[OrderResponse])
def all_orders(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    orders = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.menu_item))
        .order_by(Order.created_at.desc())
        .all()
    )
    return [serialize_order(o) for o in orders]


@router.put("/{order_id}/status", response_model=OrderResponse)
def update_status(
    order_id: int,
    request: StatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    order = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.menu_item))
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = request.status
    db.commit()
    db.refresh(order)
    return serialize_order(order)
