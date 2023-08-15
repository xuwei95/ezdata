import json

from web_apps.alert.db_models import AlertStrategy, Alert
from web_apps import db
from utils.common_utils import gen_uuid, md5, parse_json
from web_apps.alert.services.alert_forward_service import handle_alert_forward


def handle_task_fail_alert(task_conf):
    '''
    处理任务失败告警
    :return:
    '''
    print(task_conf)
    alert_strategy_ids = task_conf.get('alert_strategy_ids', '')
    alert_strategy_ids = alert_strategy_ids.split(',')
    alert_strategy_objs = db.session.query(AlertStrategy).filter(AlertStrategy.status == 1).filter(AlertStrategy.id.in_(alert_strategy_ids)).all()
    for alert_strategy_obj in alert_strategy_objs:
        task_info = task_conf.get('task_info')
        task_type = task_conf.get('type')
        task_type_map = {
            'normal_task': '普通任务',
            'dag_task': '任务工作流',
            'dag_node_task': '任务工作流节点任务',
        }
        task_name = task_info.get('name')
        trigger_conf = parse_json(alert_strategy_obj.trigger_conf)
        alert_content = f"{task_type_map.get(task_type)}失败告警:{task_name} 在重试{task_conf.get('retries')}次后仍失败。任务报错：{task_conf.get('exception_file')}:{task_conf.get('exception_line')}:{task_conf.get('exception')}"
        alert_level = trigger_conf.get('level')
        alert_source = task_conf.get('worker')
        alert_tags = {
            'task_uuid': task_conf.get('task_uuid'),
            'worker': task_conf.get('worker'),
            'retries': task_conf.get('retries'),
        }
        alert_id = gen_uuid()
        alert_obj = Alert(
            id=alert_id,
            strategy_id=alert_strategy_obj.id,
            title=alert_strategy_obj.name,
            content=alert_content,
            level=alert_level,
            status=0,
            rule_id=md5(alert_strategy_obj.id + alert_id),
            rule_name=alert_strategy_obj.name,
            biz=task_conf.get('biz', 'scheduler'),
            source=alert_source,
            tags=json.dumps(alert_tags),
            metric=task_conf.get('metric', 'task_fail'),
            create_by='system'
        )
        db.session.add(alert_obj)
        db.session.flush()
        # 处理告警转发
        forward_conf_list = parse_json(alert_strategy_obj.forward_conf)
        handle_alert_forward(alert_obj, forward_conf_list)