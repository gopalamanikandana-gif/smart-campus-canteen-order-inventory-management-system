# Presentation Content

## Slide 1 — Smart Campus Canteen
Secure Order & Inventory Management

## Slide 2 — Problem
Campus canteens need reliable order validation and inventory consistency.
Incorrect quantities, stale stock and unauthorized management actions can
produce incorrect orders.

## Slide 3 — Solution
A React + FastAPI application that validates orders before atomically updating
inventory.

## Slide 4 — Architecture
React -> FastAPI -> SQLAlchemy -> SQLite

## Slide 5 — Core Rules
- operating hours
- stock validation
- quantity limit
- availability
- database-side price
- authentication/authorization

## Slide 6 — Testing
Show normal, edge, invalid and security tests.
Show deliberate red run.

## Slide 7 — AI Change Loop
Show:
feature request -> AI implementation -> failed tests -> AI diagnosis -> fix -> green tests.

## Slide 8 — Results
Working application, automated tests, documented architecture/design/user guide,
and honest record of failures and fixes.
