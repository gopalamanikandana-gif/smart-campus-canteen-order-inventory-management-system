"""
MENU tests.

Covers:
  7. Menu items can be viewed
  8. Menu search works
  9. Unavailable/out-of-stock items cannot be ordered
"""
from tests.conftest import create_menu_item


# 7. Menu items can be viewed ---------------------------------------------------

def test_menu_page_lists_available_items(client, menu_item):
    response = client.get("/menu")
    assert response.status_code == 200
    assert menu_item["name"].encode() in response.data


def test_menu_page_does_not_list_unavailable_items(client, app, unavailable_item):
    response = client.get("/menu")
    assert response.status_code == 200
    assert unavailable_item["name"].encode() not in response.data


def test_menu_is_viewable_without_login(client, menu_item):
    # Menu browsing itself is public; only ordering requires auth.
    response = client.get("/menu")
    assert response.status_code == 200
    assert b"Login to order" in response.data


# 8. Menu search works ------------------------------------------------------------

def test_menu_search_returns_matching_items(client, app):
    with app.app_context():
        create_menu_item(name="Veg Fried Rice", price=80, stock=10)
        create_menu_item(name="Masala Dosa", price=55, stock=10)

    response = client.get("/menu?q=Dosa")
    assert response.status_code == 200
    assert b"Masala Dosa" in response.data
    assert b"Veg Fried Rice" not in response.data


def test_menu_search_is_case_insensitive(client, app):
    with app.app_context():
        create_menu_item(name="Fresh Lime Juice", price=30, stock=10)

    response = client.get("/menu?q=lime")
    assert response.status_code == 200
    assert b"Fresh Lime Juice" in response.data


def test_menu_search_with_no_matches_shows_empty_state(client, menu_item):
    response = client.get("/menu?q=NoSuchItemXYZ")
    assert response.status_code == 200
    assert b"No items found" in response.data


# 9. Unavailable / out-of-stock items cannot be ordered ---------------------------

def test_out_of_stock_item_cannot_be_added_to_cart(student_client, out_of_stock_item):
    response = student_client.post(
        f"/cart/add/{out_of_stock_item['id']}", follow_redirects=True
    )
    assert response.status_code == 200
    assert b"This item is out of stock." in response.data

    cart_page = student_client.get("/cart")
    assert out_of_stock_item["name"].encode() not in cart_page.data


def test_unavailable_item_cannot_be_added_to_cart_even_via_direct_request(student_client, unavailable_item):
    # Even though the menu page hides unavailable items, the server must
    # still reject a direct POST that references one (defense in depth).
    response = student_client.post(
        f"/cart/add/{unavailable_item['id']}", follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Menu item is unavailable." in response.data

    cart_page = student_client.get("/cart")
    assert unavailable_item["name"].encode() not in cart_page.data


def test_adding_nonexistent_item_to_cart_is_rejected(student_client):
    response = student_client.post("/cart/add/999999", follow_redirects=True)
    assert response.status_code == 200
    assert b"Menu item is unavailable." in response.data
