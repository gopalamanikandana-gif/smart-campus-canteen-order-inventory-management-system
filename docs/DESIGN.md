# Design Document

## Core use case: Place Order

1. User authenticates.
2. Frontend sends item IDs and quantities.
3. Backend authenticates JWT.
4. Pydantic validates the request.
5. Backend checks canteen hours.
6. Backend checks duplicate items.
7. Backend checks quantity limits.
8. Backend loads menu items from the database.
9. Backend checks availability and stock.
10. Backend calculates prices using database values.
11. Backend decreases stock.
12. Backend creates the order and order items.
13. Database transaction is committed.
14. Order response is returned.

## Error handling

| Condition | Response |
|---|---|
| Missing/invalid authentication | 401/403 |
| Invalid request body | 422 |
| Canteen closed | 400 |
| Item unavailable | 400 |
| Insufficient stock | 400 |
| Item not found | 404 |
| Duplicate registration | 409 |
| Student uses admin API | 403 |

## Data model

```text
User 1 ---- * Order
Order 1 --- * OrderItem
MenuItem 1 - * OrderItem
```

## Important design decisions

### Database-side price
The client sends only menu item IDs and quantities. The backend retrieves
the authoritative price, preventing a client from changing the price.

### Atomic inventory update
Stock is reduced only after all requested items pass validation. If validation
fails before commit, no order is created and stock is not changed.

### Role-based authorization
Admin APIs require the ADMIN role. Students cannot manage inventory.
