import flask
import sqlite3
import os
import json
import requests
import bs4
import datetime
from openai import OpenAI

flask_app = flask.Flask(__name__)


def get_zip_code(address: str):
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Microsoft Edge";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
    }
    while address:
        url = f"https://www.youbianku.com/{address}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = bs4.BeautifulSoup(response.text, "html.parser")
            heading_element = soup.find("h1", id="firstHeading", class_="firstHeading")
            if heading_element:
                text = heading_element.text
                if "：" in text:
                    zip_code = text.split("：")[1]
                    return zip_code
        except Exception as e:
            # print(f"匹配错误: {e}")
            pass
        address = address[:-1]
        print(f"尝试: {address}")
    return None


@flask_app.route("/zip_code", methods=["GET"])
def zip_code_():
    request = flask.request.args
    address = request.get("address")
    zip_code = get_zip_code(address)
    if zip_code:
        return json.dumps({"zip_code": int(zip_code)})
    else:
        return json.dumps({"zip_code": -1}), 404


@flask_app.route("/")
def index():
    return (
        "这是后端!仅提供API给前端调用,请查看打开方式是否正确.\n或许看看README会有帮助?"
    )


@flask_app.route("/add_record", methods=["GET"])
def add_record():
    db = get_db()
    conn = db[0]
    curs = db[1]
    request = flask.request.args
    info = request.get("info")
    call_sign = request.get("call_sign")

    conn.execute(
        """\
INSERT OR REPLACE INTO record (call_sign,original_address,add_time) VALUES (?,?,?)""",
        (call_sign, info, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    return json.dumps(
        {
            "status": 200,
            "info": "ok",
            "call_sign": call_sign,
        }
    )


@flask_app.route("/llm", methods=["GET"])
def llm():
    db = get_db()
    conn = db[0]
    curs = db[1]

    # Fetch all records where address is missing
    data = conn.execute(
        """\
SELECT * FROM record WHERE address IS NULL"""
    ).fetchall()

    if not data:
        return json.dumps(
            {"status": 404, "info": "No records found with missing address"}
        )

    original_addresses = [row["original_address"] for row in data]
    call_signs = [row["call_sign"] for row in data]
    data = "\n".join(original_addresses)

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": "你现在是一个信息提取器,从用户给到你的字段中提取并按以下格式输出:[收件人昵称 手机号 邮编 省名 完整地址 中国业余无线电呼号],不要输出其他任何内容,包括说明,如果该信息在用户提供给你的数据中不存在,就使用NULL代替,有多行消息就依次多行输出",
            },
            {
                "role": "user",
                "content": data,
            },
        ],
        stream=False,
    )

    ai_data = response.choices[0].message.content
    print(ai_data)
    # Process the AI response and update the database
    for line, call_sign in zip(ai_data.splitlines(), call_signs):
        fields = line.split()
        if len(fields) == 6:
            name, phone, zip_code, province, address, _ = fields
            conn.execute(
                """\
UPDATE record
SET name = ?, phone = ?, zip_code = ?, province = ?, address = ?
WHERE call_sign = ?""",
                (name, phone, zip_code, province, address, call_sign),
            )

    conn.commit()

    return json.dumps(
        {"status": 200, "info": "Processed successfully", "data": ai_data}
    )


def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    return conn, curs


def init_db():
    db = get_db()
    conn = db[0]
    curs = db[1]
    conn.execute(
        """\
CREATE TABLE IF NOT EXISTS record (
    call_sign TEXT PRIMARY KEY,
    province TEXT NULL,
    address TEXT NULL,
    phone TEXT NULL,
    name TEXT NULL,
    zip_code TEXT NULL,
    status TEXT,
    add_time TEXT,
    send_time TEXT NULL,
    receipt_time TEXT NULL,
    reissue_time TEXT NULL,
    original_address TEXT
    )
"""
    )


if __name__ == "__main__":

    init_db()
    client = OpenAI(
        api_key="你的Deepseek密钥",
        base_url="https://api.deepseek.com",
    )
    flask_app.run("0.0.0.0", debug=False, port=5000)
