import json
from models import Notice, User
from web_apps import db
from utils.common_utils import parse_json, format_date, request_url
from web_apps.notice.services import NoticeSendService
from etl.utils.kafka_utils import Producer


def handle_alert_forward(alert_obj, forward_conf_list):
    '''
    处理告警转发
    :return:
    '''
    print(forward_conf_list)
    for forward_conf in forward_conf_list:
        try:
            print(forward_conf)
            forward_type = forward_conf.get('type')
            if forward_type == 'notice':
                # 转通知
                notice_users = forward_conf.get('notice_users').split(',')
                user_list = db.session.query(User).filter(User.username.in_(notice_users), User.del_flag == 0).all()
                user_ids = [str(i.id) for i in user_list]
                print(notice_users, user_ids)
                notice_obj = Notice(
                    title=alert_obj.title,
                    msg_content=alert_obj.content,
                    start_time=format_date(alert_obj.create_time, res_type='timestamp'),
                    sender=alert_obj.create_by,
                    priority='M',
                    msg_category=2,
                    msg_type='USER',
                    user_ids=json.dumps(user_ids),
                    msg_abstract='系统告警转通知'
                )
                db.session.add(notice_obj)
                db.session.commit()
                db.session.flush()
                NoticeSendService().handle_notice(notice_obj, is_sys=True)
            if forward_type == 'webhook':
                # webhook转发
                webhook_url = forward_conf.get('webhook_url')
                webhook_method = forward_conf.get('webhook_method', 'POST')
                webhook_header = parse_json(forward_conf.get('webhook_header', {}), {})
                alert_json = alert_obj.to_dict()
                res = request_url(url=webhook_url, json=alert_json, method=webhook_method, headers=webhook_header)
                print(res, alert_json)
            if forward_type == 'kafka':
                # kafka转发
                topic = forward_conf.get('topic')
                producer = Producer(topic, **{'bootstrap_servers': forward_conf.get('bootstrap_servers')})
                alert_json = json.dumps(alert_obj.to_dict(), ensure_ascii=False)
                print(alert_json)
                producer.send(alert_json)
        except Exception as e:
            print(e)
