# Architecture Document

## 1. Overview

The system is a small three-layer web application.

```text
React UI
   |
   | HTTP/JSON
   v
FastAPI API
   |
   | SQLAlchemy
   v
SQLite
```

## 2. Components

### React frontend
Responsible for:
- authentication UI
- menu display
- cart state
- order submission
- order history

### FastAPI backend
Responsible for:
- authentication
- authorization
- input validation
- business rules
- order processing
- inventory consistency

### SQLite
Stores:
- users
- menu items
- orders
- order items

## 3. Why this stack

The assessment gives one week and requires another person to run the repository.
React + FastAPI + SQLite keeps setup lightweight while still demonstrating a
real frontend/backend architecture.

## 4. Data flow

```text
Student
  |
React
  |
POST /orders
  |
JWT authentication
  |
Pydantic validation
  |
Order service
  |
Stock + price checks
  |
Database transaction
  |
Order response
  |
React
```

## 5. Security

- hashed passwords
- JWT-protected routes
- admin role checks
- backend-side price calculation
- validated request bodies
- no secrets committed
- restricted CORS
