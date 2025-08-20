from flask_login import login_required, current_user
from flask import render_template
from . import bp

@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)

