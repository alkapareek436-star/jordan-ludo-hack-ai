import os
import hmac
import sqlite3
from functools import wraps
from flask import Flask, request, jsonify, session, redirect
from dotenv import load_dotenv


load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "local-test-only-key")

DB_PATH = "payments.db"

PLANS = {
    "3_days": {"amount": 699, "days": 3},
    "5_days": {"amount": 999, "days": 5},
    "30_days": {"amount": 1999, "days": 30},
    "lifetime": {"amount": 4999, "days": None},
}

def connect_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

with connect_db() as con:
    con.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT NOT NULL,
            plan TEXT NOT NULL,
            amount INTEGER NOT NULL,
            utr TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TEXT
        )
    """)

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect("/admin/login")
        return fn(*args, **kwargs)
    return wrapper

@app.get("/")
def home():
    return "Jordan Ludo backend is running!"

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

@app.get("/admin/login")
def login_page():
    return """
    <h2>Jordan Admin Login</h2>
    <form method="post">
      <input name="username" placeholder="Username" required>
      <input name="password" type="password" placeholder="Password" required>
      <button type="submit">Login</button>
    </form>
    """

@app.post("/admin/login")
def login():
    username = os.environ.get("ADMIN_USERNAME")
    password = os.environ.get("ADMIN_PASSWORD")

    if not username or not password:
        return "Admin credentials are not configured.", 503

    if (hmac.compare_digest(request.form.get("username", ""), username)
            and hmac.compare_digest(request.form.get("password", ""), password)):
        session["admin"] = True
        return redirect("/admin")

    return "Invalid login.", 401

@app.post("/admin/logout")
def logout():
    session.clear()
    return redirect("/admin/login")

@app.get("/admin")
@admin_required
def admin_dashboard():
    from html import escape

    with connect_db() as con:
        rows = con.execute(
            "SELECT * FROM payments ORDER BY id DESC"
        ).fetchall()

    total = len(rows)
    pending = sum(1 for r in rows if r["status"] == "Pending")
    approved = sum(1 for r in rows if r["status"] == "Approved")
    rejected = sum(1 for r in rows if r["status"] == "Rejected")

    table_rows = ""

    for r in rows:
        status = escape(str(r["status"]))
        status_class = {
            "Pending": "pending",
            "Approved": "approved",
            "Rejected": "rejected"
        }.get(status, "pending")

        table_rows += f"""
        <tr>
          <td>#{r['id']}</td>
          <td>{escape(str(r['telegram_id']))}</td>
          <td>{escape(str(r['plan']))}</td>
          <td class="amount">₹{r['amount']:,}</td>
          <td class="utr">{escape(str(r['utr']))}</td>
          <td><span class="status {status_class}">{status}</span></td>
          <td>
            {f'''
            <form class="actions" method="post"
                  action="/admin/review/{r['id']}">
              <button class="approve" name="decision"
                      value="Approved">✓ Approve</button>
              <button class="reject" name="decision"
                      value="Rejected">✕ Reject</button>
            </form>
            ''' if status == "Pending" else '<span class="reviewed">Reviewed</span>'}
          </td>
        </tr>
        """

    if not table_rows:
        table_rows = """
        <tr><td colspan="7" class="empty">
          <div class="empty-icon">◈</div>
          <h3>No Payment Requests Yet</h3>
          <p>New payment submissions will appear here.</p>
        </td></tr>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>JORDAN | Admin Dashboard</title>
<style>
*{{box-sizing:border-box}}
:root{{
  --bg:#070916;--panel:#101429;--line:#26294a;
  --blue:#00e5ff;--purple:#a855f7;--text:#f4f5ff;
  --muted:#9298b8
}}
body{{
  margin:0;background:
  radial-gradient(ellipse at 10% 0%,#17205b66,transparent 40%),
  radial-gradient(ellipse at 95% 15%,#57117a44,transparent 35%),
  var(--bg);color:var(--text);
  font-family:Segoe UI,Arial,sans-serif;min-height:100vh
}}
header{{
  display:flex;justify-content:space-between;align-items:center;
  gap:15px;padding:20px 5%;border-bottom:1px solid var(--line);
  background:#090b1acc;backdrop-filter:blur(12px)
}}
.brand{{display:flex;align-items:center;gap:12px}}
.logo{{
  width:45px;height:45px;display:grid;place-items:center;
  border:1px solid var(--blue);border-radius:13px;color:var(--blue);
  font-size:24px;text-shadow:0 0 15px var(--blue);
  box-shadow:0 0 18px #00e5ff25
}}
.brand h2{{margin:0;font-size:18px;letter-spacing:2px}}
.brand small{{display:block;color:var(--blue);font-size:10px;
  letter-spacing:3px;margin-top:5px}}
.logout{{
  border:1px solid #fb557b88;background:#fb557b12;color:#ff7895;
  border-radius:9px;padding:10px 15px;cursor:pointer;font-weight:600
}}
main{{max-width:1450px;margin:auto;padding:32px 5% 50px}}
.eyebrow{{color:var(--blue);letter-spacing:3px;font-size:11px;font-weight:bold}}
h1{{font-size:clamp(25px,4vw,38px);margin:10px 0}}
h1 span{{color:var(--blue);text-shadow:0 0 20px #00e5ff55}}
.subtitle{{color:var(--muted);font-size:14px;line-height:1.6}}
.stats{{
  display:grid;grid-template-columns:repeat(4,minmax(0,1fr));
  gap:16px;margin:28px 0
}}
.stat{{
  background:linear-gradient(145deg,#151a35,#0d1022);
  border:1px solid var(--line);border-radius:15px;padding:20px;
  position:relative;overflow:hidden
}}
.stat:after{{content:"";position:absolute;top:0;left:0;width:100%;
  height:2px;background:var(--glow)}}
.stat-label{{color:var(--muted);font-size:12px}}
.stat-value{{font-size:30px;font-weight:750;margin-top:12px}}
.stat-icon{{float:right;font-size:21px;color:var(--glow);
  text-shadow:0 0 15px var(--glow)}}
.cyan{{--glow:#00e5ff}}.violet{{--glow:#b56bff}}
.green{{--glow:#36f5a1}}.red{{--glow:#ff6688}}
.panel{{
  border:1px solid var(--line);border-radius:17px;
  background:#0d1022ed;overflow:hidden;
  box-shadow:0 0 35px #5342ff0b
}}
.panel-head{{
  display:flex;justify-content:space-between;align-items:center;
  gap:12px;padding:22px;border-bottom:1px solid var(--line)
}}
.panel-head h2{{margin:0;font-size:17px}}
.live{{color:#47f5ad;font-size:11px;letter-spacing:1px}}
.live:before{{content:"●";margin-right:7px;text-shadow:0 0 8px #47f5ad}}
.table-wrap{{overflow-x:auto}}
table{{width:100%;border-collapse:collapse;min-width:850px}}
th{{text-align:left;padding:15px;color:#9298b8;font-size:10px;
  letter-spacing:1px;background:#14172b}}
td{{padding:17px 15px;border-top:1px solid #222641;font-size:12px}}
tbody tr:hover{{background:#171a33}}
.amount{{color:var(--blue);font-weight:700}}
.utr{{font-family:Consolas,monospace;color:#d1c5ff}}
.status{{display:inline-block;border-radius:30px;padding:6px 10px;
  font-size:10px;font-weight:bold}}
.pending{{color:#ffd36b;background:#ffd36b16;border:1px solid #ffd36b44}}
.approved{{color:#43f5a3;background:#43f5a316;border:1px solid #43f5a344}}
.rejected{{color:#ff7895;background:#ff789516;border:1px solid #ff789544}}
.actions{{display:flex;gap:7px}}
.actions button{{border-radius:7px;padding:8px 10px;font-size:11px;
  cursor:pointer;font-weight:bold;white-space:nowrap}}
.approve{{color:#43f5a3;background:#43f5a310;border:1px solid #43f5a366}}
.approve:hover{{background:#43f5a325;box-shadow:0 0 12px #43f5a322}}
.reject{{color:#ff7895;background:#ff789510;border:1px solid #ff789566}}
.reject:hover{{background:#ff789525}}
.reviewed{{color:var(--muted);font-size:11px}}
.empty{{text-align:center;padding:55px 15px;color:var(--muted)}}
.empty-icon{{font-size:36px;color:var(--purple);text-shadow:0 0 20px var(--purple)}}
.empty h3{{color:var(--text)}}
footer{{text-align:center;color:#656b8c;font-size:11px;padding:25px}}
@media(max-width:760px){{
  main{{padding:25px 4%}}
  header{{padding:16px 4%}}
  .stats{{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}}
  .stat{{padding:15px}}
  .stat-value{{font-size:25px}}
  .panel-head{{padding:17px}}
  .brand h2{{font-size:14px}}
}}
</style>
</head>
<body>
<header>
  <div class="brand">
    <div class="logo">♟</div>
    <div>
      <h2>JORDAN <span style="color:#00e5ff">LUDO</span></h2>
      <small>CONTROL CENTER</small>
    </div>
  </div>
  <form method="post" action="/admin/logout">
    <button class="logout">↪️ Logout</button>
  </form>
</header>

<main>
  <div class="eyebrow">ADMINISTRATION / OVERVIEW</div>
  <h1>Admin <span>Dashboard</span></h1>
  <p class="subtitle">Manage payment requests and review UTR details.</p>
<div style="margin:20px 0;">
    <a href="/admin/payment-settings"
       style="display:inline-block;padding:12px 20px;
       background:#00e5ff;color:#070916;text-decoration:none;
       border-radius:9px;font-weight:bold;">
      ⚙️ Payment Settings
    </a>
  </div>

  <section class="stats">
    <div class="stat cyan">
      <span class="stat-icon">◈</span>
      <div class="stat-label">TOTAL REQUESTS</div>
      <div class="stat-value">{total}</div>
    </div>
    <div class="stat violet">
      <span class="stat-icon">◷</span>
      <div class="stat-label">PENDING REVIEW</div>
      <div class="stat-value">{pending}</div>
    </div>
    <div class="stat green">
      <span class="stat-icon">✓</span>
      <div class="stat-label">APPROVED</div>
      <div class="stat-value">{approved}</div>
    </div>
    <div class="stat red">
      <span class="stat-icon">✕</span>
      <div class="stat-label">REJECTED</div>
      <div class="stat-value">{rejected}</div>
    </div>
  </section>

  <section class="panel">
    <div class="panel-head">
      <h2>◈ Payment Requests</h2>
      <span class="live">ADMIN VIEW</span>
    </div>
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th>ID</th><th>TELEGRAM ID</th><th>PLAN</th>
          <th>AMOUNT</th><th>UTR NUMBER</th><th>STATUS</th><th>ACTION</th>
        </tr></thead>
        <tbody>{table_rows}</tbody>
      </table>
    </div>
  </section>
  <p class="subtitle" style="margin-top:18px">
    ⚠️ Verify the payment in your UPI app before approving any request.
  </p>
</main>
<footer>JORDAN LUDO • ADMIN CONTROL CENTER</footer>
</body>
</html>"""

@app.post("/admin/review/<int:payment_id>")
@admin_required
def review_payment(payment_id):
    decision = request.form.get("decision")
    if decision not in ("Approved", "Rejected"):
        return "Invalid decision", 400

    with connect_db() as con:
        cur = con.execute(
            """UPDATE payments SET status=?, reviewed_at=CURRENT_TIMESTAMP
               WHERE id=? AND status='Pending'""",
            (decision, payment_id)
        )
        if cur.rowcount == 0:
            return "Payment not found or already reviewed.", 409

    return redirect("/admin")

@app.post("/api/payments")
def create_payment():
    data = request.get_json(silent=True) or {}
    telegram_id = str(data.get("telegram_id", "")).strip()
    plan_key = str(data.get("plan", "")).strip()
    utr = str(data.get("utr", "")).strip()

    if not telegram_id or not utr or plan_key not in PLANS:
        return jsonify({"error": "Telegram ID, valid plan and UTR are required."}), 400

    if not 6 <= len(utr) <= 40:
        return jsonify({"error": "Please check the UTR value."}), 400

    try:
        with connect_db() as con:
            cur = con.execute(
                "INSERT INTO payments (telegram_id, plan, amount, utr) VALUES (?, ?, ?, ?)",
                (telegram_id, plan_key, PLANS[plan_key]["amount"], utr)
            )
    except sqlite3.IntegrityError:
        return jsonify({"error": "This UTR has already been submitted."}), 409

    return jsonify({
        "payment_id": cur.lastrowid,
        "status": "Pending",
        "message": "Request received for admin verification."
    }), 201

if __name__ == "__main__":
    app.run(debug=True)