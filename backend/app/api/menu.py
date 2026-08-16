from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..auth import require_admin
from ..database import get_db
from ..models import MenuItem, User
from ..schemas import MenuCreate, MenuResponse, MenuUpdate

router = APIRouter(prefix="/menu", tags=["menu"])


@router.get("", response_model=list[MenuResponse])
def list_menu(db: Session = Depends(get_db)):
    return db.query(MenuItem).order_by(MenuItem.id).all()


@router.post("", response_model=MenuResponse, status_code=201)
def create_menu(
    request: MenuCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    item = MenuItem(**request.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=MenuResponse)
def update_menu(
    item_id: int,
    request: MenuUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    item = db.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    for key, value in request.model_dump(exclude_unset=True).items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return item
