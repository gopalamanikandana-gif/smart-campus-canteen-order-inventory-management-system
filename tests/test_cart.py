"""
CART tests.

Covers:
  10. Student can add an available item to cart
  11. Cart quantity can be updated
  12. Cart item can be removed
  13. Empty cart is handled correctly
  14. Quantity cannot exceed available stock
"""


# 10. Student can add an available item to cart ------------------------------

def test_add_available_item_to_cart(student_client, menu_item):
    response = student_client.post(f"/cart/add/{menu_item['id']}", follow_redirects=True)
    assert response.status_code == 200
    assert b"added to cart" in response.data

    cart_page = student_client.get("/cart")
    assert menu_item["name"].encode() in cart_page.data


def test_adding_same_item_twice_increments_quantity(student_client, menu_item):
    student_client.post(f"/cart/add/{menu_item['id']}", follow_redirects=True)
    student_client.post(f"/cart/add/{menu_item['id']}", follow_redirects=True)

    with student_client.session_transaction() as sess:
        assert sess["cart"][str(menu_item["id"])] == 2


# 11. Cart quantity can be updated --------------------------------------------

def test_cart_quantity_can_be_updated(student_client, menu_item):
    student_client.post(f"/cart/add/{menu_item['id']}", follow_redirects=True)

    response = student_client.post(
        "/cart/update",
        data={f"qty_{menu_item['id']}": "3"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Cart updated." in response.data

    with student_client.session_transaction() as sess:
        assert sess["cart"][str(menu_item["id"])] == 3

    cart_page = student_client.get("/cart")
    expected_subtotal = f"{menu_item['price'] * 3:.2f}".encode()
    assert expected_subtotal in cart_page.data


# 12. Cart item can be removed -------------------------------------------------

def test_cart_item_can_be_removed(student_client, menu_item):
    student_client.post(f"/cart/add/{menu_item['id']}", follow_redirects=True)
    cart_page = student_client.get("/cart")
    assert menu_item["name"].encode() in cart_page.data

    response = student_client.post(f"/cart/remove/{menu_item['id']}", follow_redirects=True)
    assert response.status_code == 200

    cart_page_after = student_client.get("/cart")
    assert menu_item["name"].encode() not in cart_page_after.data
    assert b"Your cart is empty" in cart_page_after.data


# 13. Empty cart is handled correctly ------------------------------------------

def test_empty_cart_shows_empty_state(student_client):
    response = student_client.get("/cart")
    assert response.status_code == 200
    assert b"Your cart is empty" in response.data


def test_placing_order_with_empty_cart_is_rejected(student_client):
    response = student_client.post("/orders/place", follow_redirects=True)
    assert response.status_code == 200
    assert b"Your cart is empty." in response.data


def test_update_cart_with_zero_quantity_removes_item(student_client, menu_item):
    """A quantity of 0 (an 'invalid quantity') should drop the line, not crash."""
    student_client.post(f"/cart/add/{menu_item['id']}", follow_redirects=True)

    student_client.post(
        "/cart/update",
        data={f"qty_{menu_item['id']}": "0"},
        follow_redirects=True,
    )

    with student_client.session_transaction() as sess:
        assert str(menu_item["id"]) not in sess["cart"]


# 14. Quantity cannot exceed available stock ------------------------------------

def test_adding_item_beyond_stock_is_capped(student_client, low_stock_item):
    # low_stock_item has stock=2; add it 5 times in a row. The request that
    # pushes the running quantity past stock (the 3rd add) is the one that
    # carries the "Only N unit(s) available." flash message.
    last_response = None
    for _ in range(5):
        last_response = student_client.post(
            f"/cart/add/{low_stock_item['id']}", follow_redirects=True
        )

    assert b"Only 2 unit(s) available." in last_response.data

    with student_client.session_transaction() as sess:
        assert sess["cart"][str(low_stock_item["id"])] == low_stock_item["stock"]


def test_cart_update_caps_quantity_to_available_stock(student_client, low_stock_item):
    student_client.post(f"/cart/add/{low_stock_item['id']}", follow_redirects=True)

    student_client.post(
        "/cart/update",
        data={f"qty_{low_stock_item['id']}": "999"},
        follow_redirects=True,
    )

    with student_client.session_transaction() as sess:
        assert sess["cart"][str(low_stock_item["id"])] == low_stock_item["stock"]
