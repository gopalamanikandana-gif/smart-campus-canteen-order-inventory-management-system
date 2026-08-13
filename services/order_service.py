from models import db, MenuItem, Order, OrderItem

def create_order_from_cart(user_id, cart_data):
    if not cart_data:
        raise ValueError("Your cart is empty.")

    order = Order(user_id=user_id, status="Pending", total=0)
    db.session.add(order)
    total = 0.0

    for key, raw_qty in cart_data.items():
        try:
            item_id = int(key)
            quantity = int(raw_qty)
        except (TypeError, ValueError):
            raise ValueError("Invalid cart data.")

        if quantity <= 0:
            raise ValueError("Invalid quantity.")
        item = db.session.get(MenuItem, item_id)
        if not item or not item.is_available:
            raise ValueError("One of the selected items is unavailable.")
        if item.stock < quantity:
            raise ValueError(f"Not enough stock for {item.name}. Available: {item.stock}.")

        # Always use the current database price, never a client-submitted price.
        unit_price = float(item.price)
        subtotal = round(unit_price * quantity, 2)
        item.stock -= quantity
        item.is_available = item.stock > 0

        order.items.append(OrderItem(
            menu_item_id=item.id,
            item_name=item.name,
            unit_price=unit_price,
            quantity=quantity,
            subtotal=subtotal
        ))
        total += subtotal

    order.total = round(total, 2)
    return order
