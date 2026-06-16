"""
告警渠道分发

按 forward_conf 中每一项的 type 分发到对应渠道。渠道实现为同步函数(供 Celery worker 调用)。
内置渠道：webhook / kafka / email / notice；可通过 register_channel 扩展。

格式参考 ezdata(api/web_apps/alert)：
- webhook：POST 告警记录的完整 JSON(alert.to_dict())到 webhook_url；
- kafka：将告警记录 JSON 字符串发送到 topic；
- email：标题+内容通过 SMTP 发送；
- notice：转为系统通知(sys_notice)，通知指定用户(用户名写入通知内容)。
"""

import json
import smtplib
from email.mime.text import MIMEText
from typing import Any, Callable

from loguru import logger as loguru_logger

# 渠道发送器注册表：type -> sender(record: dict, conf: dict)
_channels: dict[str, Callable[[dict[str, Any], dict[str, Any]], None]] = {}


def register_channel(channel_type: str):
    """注册告警渠道发送器"""

    def _decorator(func: Callable[[dict[str, Any], dict[str, Any]], None]):
        _channels[channel_type] = func
        return func

    return _decorator


def dispatch_forward(record: dict[str, Any], forward_conf_list: list[dict[str, Any]]) -> None:
    """按转发配置列表分发告警(单个渠道失败不影响其他渠道)"""
    for conf in forward_conf_list or []:
        ctype = conf.get('type')
        sender = _channels.get(ctype)
        if sender is None:
            loguru_logger.warning(f'未知告警渠道类型: {ctype}')
            continue
        try:
            sender(record, conf)
            loguru_logger.info(f'告警渠道[{ctype}]发送成功: {record.get("title")}')
        except Exception as e:  # noqa: BLE001
            loguru_logger.error(f'告警渠道[{ctype}]发送失败: {e}')


def _alert_json(record: dict[str, Any]) -> str:
    """告警记录序列化为 JSON 字符串(对齐 ezdata 的 alert.to_dict())"""
    return json.dumps(record, ensure_ascii=False, default=str)


def _text_content(record: dict[str, Any]) -> str:
    return f"{record.get('title', '告警')}\n{record.get('content', '')}"


@register_channel('webhook')
def _send_webhook(record: dict[str, Any], conf: dict[str, Any]) -> None:
    """通用 Webhook：将告警记录 JSON 以指定方法投递到 webhook_url"""
    url = conf.get('webhook_url') or conf.get('url')
    if not url:
        raise ValueError('webhook 缺少 webhook_url')
    method = (conf.get('webhook_method') or 'POST').upper()
    headers = conf.get('webhook_header') or conf.get('headers') or {}
    if isinstance(headers, str):
        headers = json.loads(headers) if headers else {}

    import httpx

    with httpx.Client(timeout=10) as client:
        client.request(method, url, json=record, headers=headers)


@register_channel('kafka')
def _send_kafka(record: dict[str, Any], conf: dict[str, Any]) -> None:
    """Kafka：将告警记录 JSON 字符串发送到 topic(对齐 ezdata)"""
    topic = conf.get('topic')
    servers = conf.get('bootstrap_servers')
    if not topic or not servers:
        raise ValueError('kafka 缺少 topic 或 bootstrap_servers')
    from kafka import KafkaProducer  # 延迟导入，未启用 kafka 时无需安装依赖

    server_list = [s.strip() for s in str(servers).split(',') if s.strip()]
    producer = KafkaProducer(bootstrap_servers=server_list)
    try:
        producer.send(topic, _alert_json(record).encode('utf-8'))
        producer.flush()
    finally:
        producer.close()


@register_channel('notice')
def _send_notice(record: dict[str, Any], conf: dict[str, Any]) -> None:
    """转系统通知：写入 sys_notice(通知)，将告警通知到指定用户(用户名写入通知内容)。

    conf: {type:'notice', notice_users:'admin,zhangsan'}
    说明：本项目通知公告(sys_notice)为全局通知，无逐用户投递表，故将目标用户写入通知内容，
    在「系统管理-通知公告」中可见。
    """
    from datetime import datetime

    from module_admin.entity.do.notice_do import SysNotice
    from module_task_schedule.sync_db import get_sync_session_local

    users = (conf.get('notice_users') or '').strip()
    title = (record.get('title') or '告警通知')[:50]
    body = record.get('content', '')
    content = f'【告警通知】通知用户: {users}\n{body}' if users else f'【告警通知】\n{body}'

    session_local = get_sync_session_local()
    db = session_local()
    try:
        db.add(
            SysNotice(
                notice_title=title,
                notice_type='1',
                notice_content=content.encode('utf-8'),
                status='0',
                create_by='system',
                create_time=datetime.now(),
            )
        )
        db.commit()
    finally:
        db.close()


@register_channel('email')
def _send_email(record: dict[str, Any], conf: dict[str, Any]) -> None:
    """邮件(SMTP)。conf: host/port/user/password/to(逗号分隔)/use_tls"""
    host = conf.get('host')
    to = conf.get('to')
    if not host or not to:
        raise ValueError('email 缺少 host 或 to')
    port = int(conf.get('port') or 465)
    user = conf.get('user') or ''
    password = conf.get('password') or ''
    use_tls = conf.get('use_tls', True)
    recipients = [t.strip() for t in str(to).split(',') if t.strip()]

    msg = MIMEText(_text_content(record), 'plain', 'utf-8')
    msg['Subject'] = record.get('title', '告警')
    msg['From'] = user or 'alert@localhost'
    msg['To'] = ','.join(recipients)

    if use_tls and port == 465:
        server = smtplib.SMTP_SSL(host, port, timeout=15)
    else:
        server = smtplib.SMTP(host, port, timeout=15)
        if use_tls:
            server.starttls()
    try:
        if user:
            server.login(user, password)
        server.sendmail(msg['From'], recipients, msg.as_string())
    finally:
        server.quit()
