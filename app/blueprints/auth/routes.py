from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from ...extensions import db
from ...models import User, LoginLog
from . import bp

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            db.session.add(LoginLog(user_id=user.id, ip=request.remote_addr))
            db.session.commit()
            return redirect(url_for("main.dashboard"))
        flash("用户名或密码错误", "danger")
    return render_template("login.html")

@bp.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        email = request.form.get("email","").strip()
        password = request.form.get("password","")
        if not username or not email or not password:
            flash("请完整填写表单", "warning"); return render_template("register.html")
        if User.query.filter((User.username==username)|(User.email==email)).first():
            flash("用户名或邮箱已存在", "warning"); return render_template("register.html")
        u = User(username=username, email=email); u.set_password(password)
        db.session.add(u); db.session.commit()
        flash("注册成功，请登录", "success")
        return redirect(url_for("auth.login"))
    return render_template("register.html")

@bp.route("/logout")
@login_required
def logout():
    db.session.add(LoginLog(user_id=current_user.id, ip=request.remote_addr))
    db.session.commit()
    logout_user()
    return redirect(url_for("main.index"))
