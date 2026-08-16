# Smart Campus Canteen
## User Guide

**Tactive Assessment — Deliverable 4 (3 of 3)**

This guide explains how a student or a canteen admin uses the application day to day — no technical knowledge required.

---

# For Students

## 1. Create an Account

1. Open the app and click **Register**.
2. Enter your name, email, and a password (at least 6 characters).
3. Click **Register**. You'll be taken to the login page with a success message.

If your email is already registered, you'll see a message telling you so — try **Login** instead.

## 2. Log In

1. Enter your registered email and password on the **Login** page.
2. On success, you're taken straight to the **Menu**.

## 3. Browse the Menu

- The menu shows every item the canteen currently has available.
- Use the search box to find an item by name — for example, typing "dosa" shows only matching items.
- Items that are unavailable or completely sold out won't appear here at all.

## 4. Add Items to Your Cart

1. Click **Add to cart** on any menu item.
2. If you add the same item again, its quantity in the cart goes up by one.
3. You can't add more of an item than the canteen currently has in stock — if you try, you'll see a message letting you know only a certain number are available, and your cart quantity is capped at that amount.

## 5. Review and Edit Your Cart

Open **Cart** to see everything you've added, with a running subtotal per item and a total for the whole order.

- To change a quantity, update the number next to the item and save — it will also be capped at the available stock.
- To remove an item entirely, click **Remove**.
- Setting a quantity to `0` removes that item from your cart the same way.

## 6. Place Your Order

1. From the Cart page, click **Place order**.
2. The canteen checks, at that exact moment, that everything is still in stock and every item's price is pulled fresh from the canteen's records — not from what was shown when you added it to your cart. If a price changed since you added it, your order reflects the current price, not an old one.
3. If everything checks out, your order is confirmed and your cart is cleared. If something ran out in the meantime, you'll see exactly which item and how many are left, and nothing is charged.

## 7. View Your Order History

Open **My Orders** to see every order you've placed, each with its items, total, and current status:

| Status | What it means |
|---|---|
| Pending | Placed, not yet started by the canteen |
| Preparing | The canteen has started making it |
| Ready | Ready for pickup |
| Completed | Picked up / finished |
| Cancelled | Cancelled (by you or by the canteen) |

## 8. Cancel an Order (new feature)

You can cancel your own order yourself — but only under these conditions:

- The order must still say **Pending** (once the canteen starts preparing it, you can no longer self-cancel — ask the canteen staff directly).
- You must cancel within **5 minutes** of placing the order.

**To cancel:**

1. Open **My Orders**.
2. On an eligible order, you'll see a **Cancel order** button.
3. Click it and confirm.
4. The order is marked Cancelled, and everything in it goes back into the canteen's stock immediately, so other students can order it.

If the button isn't there, the order has already moved past Pending — it's too late to self-cancel that way. If you click Cancel and the window has already passed (even if the button was still showing), the system will tell you the cancellation window has expired and nothing will change.

## 9. Log Out

Click **Logout** in the top navigation at any time. You'll need to log in again to place or view orders.

---

# For Admins

## 1. Log In

Log in with your admin account. You're taken straight to the **Admin Dashboard** instead of the student menu.

## 2. Manage the Menu

From the dashboard's **Add menu item** panel:

1. Enter the item's name, category, description (optional), price, and starting stock.
2. Click **Add item**.

Prices must be greater than ₹0 and stock cannot be negative — the form won't accept invalid values.

Each existing item in the **Inventory** list can be:

- **Edited** — change its name, category, description, price, or stock directly, then **Save**. Setting stock to `0` automatically marks the item unavailable to students; raising it back above `0` makes it available again.
- **Removed** — deactivates the item so students no longer see it on the menu (its history in past orders is preserved).

## 3. Manage Orders

The **Orders** table on the dashboard shows every order across all students — who placed it, what's in it, the total, and its current status.

To move an order forward (or cancel it from the canteen side):

1. Find the order in the table.
2. Use the status control to select the new status: Pending, Preparing, Ready, Completed, or Cancelled.
3. Save — the change is reflected immediately, both on the dashboard and on the student's own order history.

Note: once you move an order out of **Pending**, the student loses the ability to self-cancel it through their own order history — from that point on, cancellation is your call as the admin.

---

# Troubleshooting

| Problem | What to check |
|---|---|
| "Invalid email or password" on login | Double-check spelling; if you forgot your password, there is currently no self-service reset — contact an admin. |
| Can't add an item to cart | It may be out of stock or have been removed from the menu since you last looked. |
| "Not enough stock" when placing an order | Someone else may have ordered the last units between you adding it to your cart and placing the order. Adjust the quantity and try again. |
| Cancel button missing on an order | The order has moved past Pending, or more than 5 minutes have passed since you placed it. |
| Admin dashboard says "Admin access required" | You're logged in as a student account, not an admin account. |
