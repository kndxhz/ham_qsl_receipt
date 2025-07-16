import flask
import sqlite3
import os
import json
import requests
import bs4
import datetime
import pytz  # 添加pytz库来处理时区
import hashlib
import secrets
from openai import OpenAI
from apscheduler.schedulers.background import BackgroundScheduler
from flask_cors import CORS  # 添加CORS支持

flask_app = flask.Flask(__name__)
CORS(flask_app)  # 启用CORS

# 设置时区
shanghai_tz = pytz.timezone("Asia/Shanghai")

# 管理员密码（在实际部署时应该使用环境变量）
ADMIN_PASSWORD = "你的密码"

# 存储有效的管理员session
admin_sessions = {}


def generate_session_token():
    """生成安全的session token"""
    return secrets.token_urlsafe(32)


def verify_admin_session(request):
    """验证管理员session"""
    session_token = request.cookies.get("admin_session")
    if not session_token or session_token not in admin_sessions:
        return False

    session_data = admin_sessions[session_token]
    # 检查session是否过期
    if datetime.datetime.now(shanghai_tz) > session_data["expires"]:
        del admin_sessions[session_token]
        return False

    return True


def admin_required(f):
    """管理员权限装饰器"""

    def wrapper(*args, **kwargs):
        if not verify_admin_session(flask.request):
            return json.dumps({"status": 401, "message": "需要管理员权限"}), 401
        return f(*args, **kwargs)

    wrapper.__name__ = f.__name__
    return wrapper


@flask_app.route("/admin/login", methods=["POST"])
def admin_login():
    """管理员登录"""
    try:
        data = flask.request.get_json()
        password = data.get("password")

        if password == ADMIN_PASSWORD:
            # 生成session token
            session_token = generate_session_token()
            expires = datetime.datetime.now(shanghai_tz) + datetime.timedelta(days=1)

            admin_sessions[session_token] = {
                "expires": expires,
                "created": datetime.datetime.now(shanghai_tz),
            }

            response = flask.make_response(
                json.dumps(
                    {
                        "status": 200,
                        "message": "登录成功",
                        "expires": expires.isoformat(),
                    }
                )
            )

            # 设置HttpOnly cookie，增加安全性
            response.set_cookie(
                "admin_session",
                session_token,
                max_age=24 * 60 * 60,  # 1天
                httponly=True,
                secure=False,  # 在生产环境中应该设为True
                samesite="Lax",
            )

            return response
        else:
            return json.dumps({"status": 401, "message": "密码错误"}), 401

    except Exception as e:
        return json.dumps({"status": 500, "message": f"登录失败: {str(e)}"}), 500


@flask_app.route("/admin/logout", methods=["POST"])
def admin_logout():
    """管理员登出"""
    session_token = flask.request.cookies.get("admin_session")
    if session_token and session_token in admin_sessions:
        del admin_sessions[session_token]

    response = flask.make_response(json.dumps({"status": 200, "message": "已登出"}))
    response.set_cookie("admin_session", "", expires=0)
    return response


@flask_app.route("/admin/verify", methods=["GET"])
def admin_verify():
    """验证管理员session是否有效"""
    if verify_admin_session(flask.request):
        return json.dumps({"status": 200, "message": "认证有效"})
    else:
        return json.dumps({"status": 401, "message": "认证无效"}), 401


# 空函数占位符，用于邮件和微信提醒
def send_email_reminder(call_sign, message):
    """邮件提醒函数（留空供用户自定义实现）"""
    # 用户自定义邮件发送逻辑
    print(f"邮件提醒: {call_sign} - {message}")
    pass


def send_wechat_reminder(call_sign, message):
    """微信提醒函数（留空供用户自定义实现）"""
    # 用户自定义微信发送逻辑
    print(f"微信提醒: {call_sign} - {message}")
    pass


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
            pass
        address = address[:-1]
    return None


@flask_app.route("/zip_code", methods=["GET"])
def zip_code_():
    request = flask.request.args
    address = request.get("address")
    if address:
        zip_code = get_zip_code(address)
        if zip_code:
            return json.dumps({"zip_code": int(zip_code)})
    return json.dumps({"zip_code": -1}), 404


@flask_app.route("/")
def index():
    return (
        "这是后端!仅提供API给前端调用,请查看打开方式是否正确.\n或许看看README会有帮助?"
    )


@flask_app.route("/add_record", methods=["GET"])
@admin_required
def add_record():
    conn, curs = get_db()
    try:
        request = flask.request.args
        info = request.get("info")
        call_sign = request.get("call_sign")

        # 使用带时区的当前时间
        current_time = datetime.datetime.now(shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")

        conn.execute(
            """INSERT OR REPLACE INTO record 
            (call_sign, info, original_address, add_time, status) 
            VALUES (?, ?, ?, ?, ?)""",
            (call_sign, info, info, current_time, "pending"),
        )
        conn.commit()
        return json.dumps({"status": 200, "info": "ok", "call_sign": call_sign})
    finally:
        conn.close()


@flask_app.route("/llm", methods=["GET"])
@admin_required
def llm():
    global client
    if client is None:
        init_openai_client()

    conn, curs = get_db()
    try:
        data = conn.execute(
            "SELECT * FROM record WHERE (name IS NULL OR address IS NULL OR phone IS NULL) AND info IS NOT NULL"
        ).fetchall()
        if not data:
            return json.dumps(
                {"status": 404, "info": "No records found with missing address"}
            )

        original_addresses = [row["info"] for row in data]  # 使用info字段
        call_signs = [row["call_sign"] for row in data]
        data_str = "\n".join(original_addresses)

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "你现在是一个信息提取器,从用户给到你的字段中提取并按以下格式输出:[收件人昵称 手机号 邮编 省名 完整地址 中国业余无线电呼号],不要输出其他任何内容,包括说明,如果该信息在用户提供给你的数据中不存在,就使用NULL代替,有多行消息就依次多行输出",
                },
                {"role": "user", "content": data_str},
            ],
            stream=False,
        )

        ai_data = response.choices[0].message.content
        if ai_data:
            print("AI分析结果:")
            print(ai_data)

            # 处理AI响应并更新数据库
            for line, row in zip(ai_data.splitlines(), data):
                fields = line.split()
                call_sign = row["call_sign"]
                if len(fields) == 6:
                    name, phone, zip_code, province, address, _ = fields
                    print(
                        f"更新呼号 {call_sign}: {name}, {phone}, {zip_code}, {province}, {address}"
                    )

                    # 如果邮编是NULL，尝试获取
                    if zip_code == "NULL":
                        zip_code = get_zip_code(address) or "NULL"

                    conn.execute(
                        """UPDATE record 
                        SET name = ?, phone = ?, zip_code = ?, province = ?, address = ? 
                        WHERE call_sign = ?""",
                        (name, phone, zip_code, province, address, call_sign),
                    )
                else:
                    print(f"呼号 {call_sign} 的AI分析结果格式错误: {line}")

            conn.commit()
            return json.dumps(
                {"status": 200, "info": "Processed successfully", "data": ai_data}
            )
        else:
            return json.dumps({"status": 404, "info": "AI analysis failed"})
    finally:
        conn.close()


@flask_app.route("/mark_sent", methods=["GET"])
@admin_required
def mark_sent():
    """标记卡片已发送"""
    conn, curs = get_db()
    try:
        call_sign = flask.request.args.get("call_sign")
        # 使用带时区的当前时间
        current_time = datetime.datetime.now(shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")

        conn.execute(
            "UPDATE record SET send_time=?, status='sent' WHERE call_sign=?",
            (current_time, call_sign),
        )
        conn.commit()

        print(f"呼号 {call_sign} 已标记为已发送")
        return json.dumps({"status": 200, "info": "标记为已发送"})
    finally:
        conn.close()


@flask_app.route("/receipt", methods=["GET"])
def receipt():
    """处理友台回执"""
    conn, curs = get_db()
    try:
        call_sign = flask.request.args.get("call_sign")
        # 使用带时区的当前时间
        current_time = datetime.datetime.now(shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")

        conn.execute(
            "UPDATE record SET receipt_time=?, status='received' WHERE call_sign=?",
            (current_time, call_sign),
        )
        conn.commit()

        # 发送提醒
        message = f"呼号{call_sign}已回执"
        send_email_reminder(call_sign, message)
        send_wechat_reminder(call_sign, message)
        print(message)

        return json.dumps({"status": 200, "info": "回执成功"})
    finally:
        conn.close()


@flask_app.route("/mark_received", methods=["GET"])
@admin_required
def mark_received():
    """管理员标记已回执"""
    conn, curs = get_db()
    try:
        call_sign = flask.request.args.get("call_sign")
        if not call_sign:
            return json.dumps({"status": 400, "message": "缺少呼号参数"})

        # 检查记录是否存在且状态为sent
        existing = conn.execute(
            "SELECT status FROM record WHERE call_sign = ?", (call_sign,)
        ).fetchone()

        if not existing:
            return json.dumps({"status": 404, "message": "记录不存在"})

        if existing[0] != "sent":
            return json.dumps(
                {
                    "status": 400,
                    "message": f"只能标记已发送状态的记录为已回执，当前状态: {existing[0]}",
                }
            )

        # 使用带时区的当前时间
        current_time = datetime.datetime.now(shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")

        conn.execute(
            "UPDATE record SET receipt_time=?, status='received' WHERE call_sign=?",
            (current_time, call_sign),
        )
        conn.commit()

        # 发送提醒
        message = f"呼号{call_sign}已被管理员标记为已回执"
        send_email_reminder(call_sign, message)
        send_wechat_reminder(call_sign, message)

        print(f"呼号 {call_sign} 已被管理员标记为已回执")
        return json.dumps({"status": 200, "message": "已标记为已回执"})
    finally:
        conn.close()


@flask_app.route("/resend", methods=["GET"])
@admin_required
def resend():
    """标记卡片需要补发"""
    conn, curs = get_db()
    try:
        call_sign = flask.request.args.get("call_sign")
        # 使用带时区的当前时间
        current_time = datetime.datetime.now(shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")

        # 先检查记录是否存在
        record = conn.execute(
            "SELECT * FROM record WHERE call_sign=?", (call_sign,)
        ).fetchone()

        if not record:
            return json.dumps({"status": 404, "info": "呼号不存在"}), 404

        # 更新记录
        conn.execute(
            "UPDATE record SET reissue_time=?, status='resend' WHERE call_sign=?",
            (current_time, call_sign),
        )
        conn.commit()

        # 发送提醒
        message = f"呼号{call_sign}需要补发"
        send_email_reminder(call_sign, message)
        send_wechat_reminder(call_sign, message)
        print(message)

        return json.dumps({"status": 200, "info": "已标记为需要补发"})
    finally:
        conn.close()


@flask_app.route("/get_expired", methods=["GET"])
@admin_required
def get_expired():
    """获取超过一个月未回执的记录"""
    conn, curs = get_db()
    try:
        # 使用带时区的当前时间
        one_month_ago = datetime.datetime.now(shanghai_tz) - datetime.timedelta(days=30)
        one_month_ago_str = one_month_ago.strftime("%Y-%m-%d %H:%M:%S")

        records = conn.execute(
            """SELECT call_sign, add_time, send_time 
            FROM record 
            WHERE status='sent' AND send_time < ?""",
            (one_month_ago_str,),
        ).fetchall()

        result = [dict(row) for row in records]
        return json.dumps({"status": 200, "data": result})
    finally:
        conn.close()


@flask_app.route("/get_resend_list", methods=["GET"])
@admin_required
def get_resend_list():
    """获取需要补发的记录列表"""
    conn, curs = get_db()
    try:
        records = conn.execute(
            "SELECT call_sign, add_time, send_time, reissue_time FROM record WHERE status='resend'"
        ).fetchall()

        result = [dict(row) for row in records]
        return json.dumps({"status": 200, "data": result})
    finally:
        conn.close()


@flask_app.route("/get_all_records", methods=["GET"])
@admin_required
def get_all_records():
    """获取所有记录"""
    conn, curs = get_db()
    try:
        records = conn.execute("SELECT * FROM record").fetchall()
        result = [dict(row) for row in records]
        return json.dumps({"status": 200, "data": result})
    finally:
        conn.close()


@flask_app.route("/delete_record", methods=["GET"])
@admin_required
def delete_record():
    """删除记录"""
    call_sign = flask.request.args.get("call_sign")
    if not call_sign:
        return json.dumps({"status": 400, "message": "缺少呼号参数"})

    conn, curs = get_db()
    try:
        # 检查记录是否存在
        existing = conn.execute(
            "SELECT call_sign FROM record WHERE call_sign = ?", (call_sign,)
        ).fetchone()

        if not existing:
            return json.dumps({"status": 404, "message": "记录不存在"})

        # 删除记录
        conn.execute("DELETE FROM record WHERE call_sign = ?", (call_sign,))
        conn.commit()

        return json.dumps({"status": 200, "message": "记录删除成功"})
    except Exception as e:
        conn.rollback()
        return json.dumps({"status": 500, "message": f"删除失败: {str(e)}"})
    finally:
        conn.close()


@flask_app.route("/edit_record", methods=["POST"])
@admin_required
def edit_record():
    """编辑记录信息"""
    try:
        data = flask.request.get_json()
        if not data:
            return json.dumps({"status": 400, "message": "请求数据为空"})

        call_sign = data.get("call_sign")
        if not call_sign:
            return json.dumps({"status": 400, "message": "缺少呼号参数"})

        conn, curs = get_db()
        try:
            # 检查记录是否存在
            existing = conn.execute(
                "SELECT call_sign FROM record WHERE call_sign = ?", (call_sign,)
            ).fetchone()

            if not existing:
                return json.dumps({"status": 404, "message": "记录不存在"})

            # 更新记录
            update_fields = []
            update_values = []

            if "name" in data:
                update_fields.append("name = ?")
                update_values.append(data["name"])
            if "phone" in data:
                update_fields.append("phone = ?")
                update_values.append(data["phone"])
            if "address" in data:
                update_fields.append("address = ?")
                update_values.append(data["address"])
            if "province" in data:
                update_fields.append("province = ?")
                update_values.append(data["province"])
            if "zip_code" in data:
                update_fields.append("zip_code = ?")
                update_values.append(data["zip_code"])
            if "info" in data:
                update_fields.append("info = ?")
                update_values.append(data["info"])

            if not update_fields:
                return json.dumps({"status": 400, "message": "没有需要更新的字段"})

            # 执行更新
            update_values.append(call_sign)
            sql = f"UPDATE record SET {', '.join(update_fields)} WHERE call_sign = ?"
            conn.execute(sql, update_values)
            conn.commit()

            return json.dumps({"status": 200, "message": "记录更新成功"})
        except Exception as e:
            conn.rollback()
            return json.dumps({"status": 500, "message": f"更新失败: {str(e)}"})
        finally:
            conn.close()
    except Exception as e:
        return json.dumps({"status": 500, "message": f"请求处理失败: {str(e)}"})


@flask_app.route("/llm_single", methods=["GET"])
@admin_required
def llm_single():
    """对单个记录进行AI地址分析"""
    global client
    if client is None:
        init_openai_client()

    call_sign = flask.request.args.get("call_sign")
    if not call_sign:
        return json.dumps({"status": 400, "message": "缺少呼号参数"})

    conn, curs = get_db()
    try:
        # 检查记录是否存在且需要处理
        record = conn.execute(
            "SELECT call_sign, info FROM record WHERE call_sign = ? AND (name IS NULL OR phone IS NULL OR address IS NULL) AND info IS NOT NULL",
            (call_sign,),
        ).fetchone()

        if not record:
            return json.dumps({"status": 404, "message": "记录不存在或已处理过"})

        # 使用AI处理地址信息
        try:
            print(f"正在处理呼号: {call_sign}")
            print(f"原始信息: {record['info']}")

            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": '你是一个地址信息解析专家。请从用户提供的地址信息中提取出姓名、电话号码、详细地址等信息，并以JSON格式返回。返回格式：{"name": "姓名", "phone": "电话", "address": "详细地址", "province": "省份"}',
                    },
                    {
                        "role": "user",
                        "content": f"请解析以下地址信息：{record['info']}",
                    },
                ],
                temperature=0.1,
            )

            result_text = response.choices[0].message.content
            print(f"AI返回原始内容: {result_text}")

            if not result_text:
                print("AI返回内容为空")
                return json.dumps({"status": 500, "message": "AI返回内容为空"})

            result_text = result_text.strip()
            print(f"AI返回清理后内容: {result_text}")
            result_text = result_text.replace("```json", "").replace("```", "")
            # 尝试解析AI返回的JSON
            try:
                ai_result = json.loads(result_text)
                print(f"JSON解析成功: {ai_result}")

                name = ai_result.get("name", "").strip()
                phone = ai_result.get("phone", "").strip()
                address = ai_result.get("address", "").strip()
                province = ai_result.get("province", "").strip()
                name = call_sign if name.strip() == "NULL" or name == None else name

                print(
                    f"提取的信息 - 姓名: {name}, 电话: {phone}, 地址: {address}, 省份: {province}"
                )

                # 获取邮编
                zip_code = ""
                if address:
                    zip_code = get_zip_code(address)
                    print(f"获取到的邮编: {zip_code}")

                # 更新数据库
                conn.execute(
                    "UPDATE record SET name=?, phone=?, address=?, province=?, zip_code=? WHERE call_sign=?",
                    (name, phone, address, province, zip_code, call_sign),
                )
                conn.commit()
                print(f"数据库更新成功")

                return json.dumps({"status": 200, "message": "AI处理完成"})

            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
                print(f"尝试解析的内容: {result_text}")
                return json.dumps({"status": 500, "message": "AI返回格式错误"})

        except Exception as e:
            print(f"AI处理失败: {str(e)}")
            return json.dumps({"status": 500, "message": f"AI处理失败: {str(e)}"})

    except Exception as e:
        return json.dumps({"status": 500, "message": f"处理失败: {str(e)}"})
    finally:
        conn.close()


def check_receipt_timeout():
    """定时检查超时未回执的记录"""
    with flask_app.app_context():
        conn, curs = get_db()
        try:
            # 使用带时区的当前时间
            one_month_ago = datetime.datetime.now(shanghai_tz) - datetime.timedelta(
                days=30
            )
            one_month_ago_str = one_month_ago.strftime("%Y-%m-%d %H:%M:%S")

            records = conn.execute(
                "SELECT call_sign FROM record WHERE status='sent' AND send_time < ?",
                (one_month_ago_str,),
            ).fetchall()

            print(f"检查超时记录，找到 {len(records)} 条记录")

            for record in records:
                call_sign = record["call_sign"]
                # 发送提醒
                message = f"呼号{call_sign}超过一个月未回执，请手动询问"
                send_email_reminder(call_sign, message)
                send_wechat_reminder(call_sign, message)
                print(message)
        except Exception as e:
            print(f"检查超时记录时出错: {str(e)}")
        finally:
            conn.close()


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn, conn.cursor()


def init_db():
    """初始化数据库"""
    conn, curs = get_db()
    try:
        conn.execute(
            """
        CREATE TABLE IF NOT EXISTS record (
            call_sign TEXT PRIMARY KEY,
            province TEXT,
            address TEXT,
            phone TEXT,
            name TEXT,
            zip_code TEXT,
            status TEXT DEFAULT 'pending',
            add_time TEXT,
            send_time TEXT,
            receipt_time TEXT,
            reissue_time TEXT,
            info TEXT,
            original_address TEXT
        )
        """
        )

        # 检查是否需要添加info字段（用于兼容旧数据库）
        try:
            conn.execute("SELECT info FROM record LIMIT 1")
        except sqlite3.OperationalError:
            # info字段不存在，添加它
            conn.execute("ALTER TABLE record ADD COLUMN info TEXT")
            # 将existing original_address data copy to info field
            conn.execute("UPDATE record SET info = original_address WHERE info IS NULL")

        conn.commit()
    finally:
        conn.close()


# 全局OpenAI客户端
client = None


def init_openai_client():
    global client
    client = OpenAI(
        api_key="你的API密钥",
        base_url="https://api.deepseek.com",
    )


if __name__ == "__main__":
    init_db()
    init_openai_client()

    # 初始化定时任务
    scheduler = BackgroundScheduler(timezone=shanghai_tz)
    scheduler.add_job(
        check_receipt_timeout, "cron", hour=9, minute=0  # 每天早上9点检查
    )
    scheduler.start()

    print("启动定时任务，每天上午9点检查超时记录")
    flask_app.run("0.0.0.0", debug=False, port=5000)
