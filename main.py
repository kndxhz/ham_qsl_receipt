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
import threading  # 添加线程支持用于后台任务
import logging
from openai import OpenAI
from apscheduler.schedulers.background import BackgroundScheduler
from flask_cors import CORS  # 添加CORS支持
import time
from urllib.parse import quote
import re
import random

flask_app = flask.Flask(__name__)
CORS(flask_app)  # 启用CORS

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # 控制台输出
        logging.FileHandler("ham_qsl.log", encoding="utf-8"),  # 文件输出
    ],
)
logger = logging.getLogger(__name__)

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
    logger.info(f"邮件提醒: {call_sign} - {message}")
    pass


def send_wechat_reminder(call_sign, message):
    """微信提醒函数（留空供用户自定义实现）"""
    # 用户自定义微信发送逻辑
    logger.info(f"微信提醒: {call_sign} - {message}")
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
        url = f"https://www.chashudi.com/search/?keyword={address}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = bs4.BeautifulSoup(response.text, "html.parser")
            # 查找指定xpath对应的元素
            # /html/body/div[1]/div[2]/div/div/div[2]/div[2]/div[2]/table/tbody/tr[1]/td[2]/a
            # 用css选择器实现
            heading_element = soup.select_one(
                "body > div.wrapper > div.container > div > div > div.bd > div:nth-child(2) > div.table-inner > table > tbody > tr:nth-child(1) > td:nth-child(2) > a"
            )

            if heading_element:
                text = heading_element.text
                return text.strip()  # 返回邮政编码
        except Exception as e:
            # print(f"匹配错误: {e}")
            pass
        logger.debug(f"尝试: {address}")
        address = address[:-1]

    return None


def get_zip_code_to_db(address: str, call_sign: str):
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
        url = f"https://www.chashudi.com/search/?keyword={address}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = bs4.BeautifulSoup(response.text, "html.parser")
            # 查找指定xpath对应的元素
            # /html/body/div[1]/div[2]/div/div/div[2]/div[2]/div[2]/table/tbody/tr[1]/td[2]/a
            # 用css选择器实现
            heading_element = soup.select_one(
                "body > div.wrapper > div.container > div > div > div.bd > div:nth-child(2) > div.table-inner > table > tbody > tr:nth-child(1) > td:nth-child(2) > a"
            )

            if heading_element:
                text = heading_element.text
                # 直接写入数据库
                conn, curs = get_db()
                try:
                    conn.execute(
                        "UPDATE record SET zip_code=? WHERE call_sign=?",
                        (text.strip(), call_sign),
                    )
                    conn.commit()
                finally:
                    conn.close()
                return text.strip()  # 返回邮政编码
        except Exception as e:
            # print(f"匹配错误: {e}")
            pass
        logger.debug(f"尝试: {address}")
        address = address[:-1]

    return None


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

        logger.info(f"呼号 {call_sign} 已标记为已发送")
        return json.dumps({"status": 200, "info": "标记为已发送"})
    finally:
        conn.close()


@flask_app.route("/check_callsign", methods=["GET"])
def check_callsign():
    """检查呼号是否存在"""
    conn, curs = get_db()
    try:
        call_sign = flask.request.args.get("call_sign")
        if not call_sign:
            return json.dumps({"status": 400, "info": "缺少呼号参数"}), 400

        # 查询呼号是否存在
        result = curs.execute(
            "SELECT call_sign FROM record WHERE call_sign=?", (call_sign,)
        ).fetchone()

        if result:
            return json.dumps({"status": 200, "exists": True, "info": "呼号存在"})
        else:
            return (
                json.dumps({"status": 404, "exists": False, "info": "呼号不存在"}),
                404,
            )
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
        logger.info(message)

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

        logger.info(f"呼号 {call_sign} 已被管理员标记为已回执")
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
        logger.info(message)

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
            logger.debug(f"正在处理呼号: {call_sign}")
            logger.debug(f"原始信息: {record['info']}")

            response = client.chat.completions.create(  # type: ignore
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": '你是一个地址信息解析专家。请从用户提供的地址信息中提取出姓名、电话号码、详细地址、邮编等信息，并以JSON格式返回。手机号不要带有+86,如果有单独一行的6位数整数则默认为邮编.返回格式：{"name": "姓名", "phone": "电话", "address": "详细地址", "province": "省份", "zip_code": "邮编"}。如果无法确定某个字段，请留空。',
                    },
                    {
                        "role": "user",
                        "content": f"请解析以下地址信息：{record['info']}",
                    },
                ],
                temperature=0.1,
            )

            result_text = response.choices[0].message.content
            logger.debug(f"AI返回原始内容: {result_text}")

            if not result_text:
                logger.error("AI返回内容为空")
                return json.dumps({"status": 500, "message": "AI返回内容为空"})

            result_text = result_text.strip()
            logger.debug(f"AI返回清理后内容: {result_text}")
            result_text = result_text.replace("```json", "").replace("```", "")
            # 尝试解析AI返回的JSON
            try:
                ai_result = json.loads(result_text)
                logger.debug(f"JSON解析成功: {ai_result}")

                name = ai_result.get("name", "").strip()
                phone = ai_result.get("phone", "").strip()
                address = ai_result.get("address", "").strip()
                province = ai_result.get("province", "").strip()
                ai_zip_code = ai_result.get("zip_code", "").strip()
                name = call_sign if name.strip() == "NULL" or name == None else name

                logger.debug(
                    f"提取的信息 - 姓名: {name}, 电话: {phone}, 地址: {address}, 省份: {province}, AI邮编: {ai_zip_code}"
                )

                # 处理邮编 - 如果AI已经提取到邮编，直接使用；否则先更新其他信息，然后后台获取邮编
                zip_code = ""
                need_background_fetch = False

                if ai_zip_code:
                    zip_code = ai_zip_code
                    logger.info(f"使用AI分析的邮编: {zip_code}")
                elif address:
                    # 如果有地址但没有AI邮编，标记需要后台获取
                    need_background_fetch = True
                    logger.info(f"需要后台获取邮编，地址: {address}")

                # 立即更新数据库中的基本信息
                conn.execute(
                    "UPDATE record SET name=?, phone=?, address=?, province=?, zip_code=? WHERE call_sign=?",
                    (name, phone, address, province, zip_code, call_sign),
                )
                conn.commit()
                logger.info(f"基本信息已更新到数据库")

                # 如果需要，启动后台任务获取邮编
                if need_background_fetch:
                    logger.info(f"启动后台任务获取邮编...")
                    thread = threading.Thread(
                        target=get_zip_code,
                        args=(address, call_sign),
                        daemon=True,
                    )
                    thread.start()

                return json.dumps(
                    {
                        "status": 200,
                        "message": "AI处理完成",
                        "zip_code_fetching": need_background_fetch,
                    }
                )

            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}")
                logger.error(f"尝试解析的内容: {result_text}")
                return json.dumps({"status": 500, "message": "AI返回格式错误"})

        except Exception as e:
            logger.error(f"AI处理失败: {str(e)}")
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

            logger.info(f"检查超时记录，找到 {len(records)} 条记录")

            for record in records:
                call_sign = record["call_sign"]
                # 发送提醒
                message = f"呼号{call_sign}超过一个月未回执，请手动询问"
                send_email_reminder(call_sign, message)
                send_wechat_reminder(call_sign, message)
                logger.warning(message)
        except Exception as e:
            logger.error(f"检查超时记录时出错: {str(e)}")
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
        api_key="你的ds api key",
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

    logger.info("启动定时任务，每天上午9点检查超时记录")
    logger.info("HAM QSL Receipt系统启动完成")
    flask_app.run("0.0.0.0", debug=False, port=5000)
