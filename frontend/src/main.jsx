import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API = "http://127.0.0.1:8000";

async function api(path, options = {}) {
  const token = localStorage.getItem("token");
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API}${path}`, { ...options, headers });
  const data = await response.json().catch(() => ({}));

  if (!response.ok) throw new Error(data.detail || "Request failed");
  return data;
}

function Auth({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");

  async function submit(e) {
    e.preventDefault();
    setError("");
    try {
      const data = await api(`/auth/${mode}`, {
        method: "POST",
        body: JSON.stringify(form),
      });
      localStorage.setItem("token", data.access_token);
      onLogin(data.user);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="auth">
      <div className="card auth-card">
        <h1>Smart Campus Canteen</h1>
        <p className="muted">Secure ordering and inventory management</p>
        <form onSubmit={submit}>
          {mode === "register" && (
            <input
              placeholder="Name"
              value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })}
              required
            />
          )}
          <input
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={e => setForm({ ...form, email: e.target.value })}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={form.password}
            onChange={e => setForm({ ...form, password: e.target.value })}
            required
          />
          {error && <div className="error">{error}</div>}
          <button>{mode === "login" ? "Login" : "Create account"}</button>
        </form>
        <button className="link-button" onClick={() => setMode(mode === "login" ? "register" : "login")}>
          {mode === "login" ? "New student? Register" : "Already have an account? Login"}
        </button>
      </div>
    </div>
  );
}

function App() {
  const [user, setUser] = useState(null);
  const [menu, setMenu] = useState([]);
  const [cart, setCart] = useState({});
  const [orders, setOrders] = useState([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      setMenu(await api("/menu"));
      setOrders(await api("/orders"));
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => {
    const saved = localStorage.getItem("token");
    if (!saved) return;
    api("/auth/me").then(setUser).catch(() => localStorage.removeItem("token"));
  }, []);

  useEffect(() => {
    if (user) load();
  }, [user]);

  function add(item) {
    setCart(prev => ({
      ...prev,
      [item.id]: Math.min((prev[item.id] || 0) + 1, 5),
    }));
  }

  function remove(item) {
    setCart(prev => {
      const next = { ...prev };
      if ((next[item.id] || 0) <= 1) delete next[item.id];
      else next[item.id]--;
      return next;
    });
  }

  const cartItems = menu
    .filter(item => cart[item.id])
    .map(item => ({ ...item, quantity: cart[item.id] }));

  const total = cartItems.reduce((sum, x) => sum + x.price * x.quantity, 0);

  async function placeOrder() {
    setError("");
    setMessage("");
    try {
      const order = await api("/orders", {
        method: "POST",
        body: JSON.stringify({
          items: cartItems.map(x => ({
            menu_item_id: x.id,
            quantity: x.quantity,
          })),
        }),
      });
      setCart({});
      setMessage(`Order #${order.id} placed successfully.`);
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  function logout() {
    localStorage.removeItem("token");
    setUser(null);
    setCart({});
    setOrders([]);
  }

  if (!user) return <Auth onLogin={setUser} />;

  return (
    <div>
      <header>
        <div>
          <strong>Smart Campus Canteen</strong>
          <span className="muted"> · {user.name}</span>
        </div>
        <button className="secondary" onClick={logout}>Logout</button>
      </header>

      <main>
        <section>
          <h2>Menu</h2>
          <div className="grid">
            {menu.map(item => (
              <div className="card" key={item.id}>
                <h3>{item.name}</h3>
                <p className="muted">{item.description}</p>
                <p><strong>₹{item.price.toFixed(2)}</strong></p>
                <p>Stock: {item.stock}</p>
                <button
                  disabled={!item.is_available || item.stock <= 0}
                  onClick={() => add(item)}
                >
                  {item.is_available && item.stock > 0 ? "Add to cart" : "Unavailable"}
                </button>
              </div>
            ))}
          </div>
        </section>

        <section className="card cart">
          <h2>Cart</h2>
          {cartItems.length === 0 ? (
            <p className="muted">Your cart is empty.</p>
          ) : (
            <>
              {cartItems.map(item => (
                <div className="cart-row" key={item.id}>
                  <span>{item.name}</span>
                  <span>
                    <button className="small" onClick={() => remove(item)}>-</button>
                    <span className="quantity">{item.quantity}</span>
                    <button className="small" onClick={() => add(item)}>+</button>
                  </span>
                  <strong>₹{(item.price * item.quantity).toFixed(2)}</strong>
                </div>
              ))}
              <hr />
              <div className="total">Total: ₹{total.toFixed(2)}</div>
              <button onClick={placeOrder}>Place Order</button>
            </>
          )}
          {message && <div className="success">{message}</div>}
          {error && <div className="error">{error}</div>}
        </section>

        <section>
          <h2>My Orders</h2>
          {orders.map(order => (
            <div className="card order" key={order.id}>
              <div>
                <strong>Order #{order.id}</strong>
                <span className="badge">{order.status}</span>
              </div>
              <p>₹{order.total_amount.toFixed(2)}</p>
              {order.items.map(item => (
                <div key={item.menu_item_id}>
                  {item.name} × {item.quantity}
                </div>
              ))}
            </div>
          ))}
        </section>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
