import flask
import sqlite3
import os


flask_app = flask.Flask(__name__)


@flask_app.route("/")
def index():
    return "这是后端!仅提供API给前端调用,请查看打开方式是否正确.或许看看README会有帮助?"


def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    return conn, cur


if __name__ == "__main__":
    flask_app.run("0.0.0.0", debug=True)
