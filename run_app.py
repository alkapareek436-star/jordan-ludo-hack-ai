from pathlib import Path
from flask import send_from_directory

from app import app, admin_required
from payment_admin import register_payment_admin

BASE_DIR = Path(__file__).resolve().parent

register_payment_admin(app, admin_required)



@app.get("/")
def user_panel():
    return send_from_directory(str(BASE_DIR), "index.html")

app.view_functions["home"] = user_panel


@app.get("/style.css")
def user_styles():
    return send_from_directory(str(BASE_DIR), "style.css")


@app.get("/app.js")
def user_script():
    return send_from_directory(str(BASE_DIR), "app.js")

@app.get("/payment_client.js")
def payment_client_script():
    return send_from_directory(str(BASE_DIR), "payment_client.js")


if __name__ == "__main__":
    app.run(debug=False)