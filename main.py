from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
import time
from datetime import datetime, timezone
import logging

app = Flask(__name__)
app.secret_key = "your_secret_key"  # 添加一个密钥用于会话管理


# 添加自定义的日期过滤器
@app.template_filter("date")
def format_date(value, format="%Y-%m-%d %H:%M:%S"):
    if value is not None:
        return datetime.fromtimestamp(value).strftime(format)
    return ""


def get_db():
    """获取数据库连接"""
    logging.info("获取数据库连接")
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect("database.db")
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    """关闭数据库连接"""
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        password = request.form.get("password")
        if password == "123456":
            session["admin_logged_in"] = True
        else:
            return "密码错误，请重试。"

    if not session.get("admin_logged_in"):
        return render_template("admin_login.html")

    status_filter = request.args.get("status")
    conn = get_db()

    if status_filter:
        cursor = conn.execute(
            "SELECT * FROM records WHERE status = ?", (status_filter,)
        )
    else:
        cursor = conn.execute("SELECT * FROM records")

    records = cursor.fetchall()

    # 转换时间戳为 datetime 对象，并且使用时区感知
    updated_records = []
    for record in records:
        # 转换为字典
        record_dict = dict(record)
        record_dict["call_sign"] = record_dict["call_sign"].upper()
        record_dict["created_at"] = datetime.fromtimestamp(
            record_dict["created_at"], timezone.utc
        )
        record_dict["updated_at"] = datetime.fromtimestamp(
            record_dict["updated_at"], timezone.utc
        )
        updated_records.append(record_dict)

    return render_template("admin.html", records=updated_records)


@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin"))


@app.route("/add_record", methods=["POST"])
def add_record():
    call_sign = request.form["call_sign"].upper()
    created_at = updated_at = int(time.time())

    conn = get_db()
    conn.execute(
        "INSERT INTO records (call_sign, status, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (call_sign, "未回执", created_at, updated_at),
    )
    conn.commit()

    return redirect(url_for("admin"))


@app.route("/delete_record/<int:id>")
def delete_record(id):
    conn = get_db()
    conn.execute("DELETE FROM records WHERE id = ?", (id,))
    conn.commit()
    return redirect(url_for("admin"))


@app.route("/update_status/<int:id>")
def update_status(id):
    conn = get_db()
    conn.execute(
        'UPDATE records SET status = "已回执", updated_at = ? WHERE id = ?',
        (int(time.time()), id),
    )
    conn.commit()
    return redirect(url_for("admin"))


@app.route("/check_call_sign", methods=["POST"])
def check_call_sign():
    call_sign = request.form["call_sign"].upper()
    conn = get_db()
    cursor = conn.execute(
        "SELECT status FROM records WHERE call_sign = ?", (call_sign,)
    )
    record = cursor.fetchone()

    if record:
        status = record["status"]
        if status == "已回执":
            return "不要在提交啦！o(>﹏<)o\n数据已经记录到后台啦！"
        else:
            conn.execute(
                "UPDATE records SET status = '已回执', updated_at = ? WHERE call_sign = ?",
                (int(time.time()), call_sign),
            )
            conn.commit()
            return "收到啦！已记录回执，期待空中相遇，73"
    else:
        return "未找到数据，请联系：755848971"


if __name__ == "__main__":
    app.run(host="0.0.0.0")
