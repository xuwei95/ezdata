'''
任务api服务
'''
import json
from web_apps import db
from utils.query_utils import get_base_query
from utils.auth import set_insert_user, set_update_user, get_auth_token_info
from utils.common_utils import gen_json_response, gen_uuid
from web_apps.task.db_models import Task, TaskTemplate, TaskInstance
from utils.web_utils import validate_params
import pandas as pd
import io
from tasks.dag_tasks import gen_params_dag
from web_apps.task.services.scheduler_interface import get_job_list, add_job, remove_job
from utils.task_util import get_task_logs


def serialize_task_model(obj, ser_type='list'):
    '''
    序列化模型数据
    :param obj:
    :param ser_type:
    :return:
    '''
    dic = obj.to_dict()
    if ser_type == 'list':
        res = {}
        for k in ['id', 'template_code', 'name', 'params', 'run_type', 'status', 'trigger_type', 'trigger_date', 'priority', 'retry', 'countdown', 'run_queue', 'running_id', 'alert_strategy_ids', 'crontab', 'create_by', 'create_time', 'update_by', 'update_time', 'del_flag', 'sort_no', 'description']:
            if k in ['params', 'trigger_date']:
                res[k] = json.loads(dic[k])
            else:
                res[k] = dic[k]
        return res
    elif ser_type == 'detail':
        for k in ['params', 'trigger_date']:
            dic[k] = json.loads(dic[k])
        for k in ['alert_strategy_ids']:
            dic[k] = str(dic[k]).split(',') if dic[k] else []
        for k in []:
            dic.pop(k)
    elif ser_type == 'all_list':
        res = {}
        for k in ['id', 'template_code', 'name']:
            res[k] = dic[k]
        return res
        
    return dic

    
class TaskApiService(object):
    def __init__(self):
        pass

    def get_instance_list(self, req_dict):
        '''
        获取任务实例列表
        '''
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        task_id = req_dict.get('task_id', '')
        task_type = req_dict.get('task_type', 'task')
        query = db.session.query(TaskInstance)
        if task_id != '':
            if task_type == 'task':
                query = query.filter(TaskInstance.task_id == task_id, TaskInstance.parent_id == '')
            else:
                query = query.filter(TaskInstance.node_id == task_id)
        query = query.order_by(TaskInstance.start_time.desc())
        total = query.count()
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = obj.to_dict()
            result.append(dic)
        res_data = {
            'records': result,
            'total': total
        }
        return gen_json_response(data=res_data)

    def get_instance_logs(self, req_dict):
        '''
        获取任务实例日志
        '''
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        task_id = req_dict.get('task_id', '')
        res_data = get_task_logs(task_id, page, pagesize)
        return res_data

    def gen_task_trigger(self, task_obj):
        '''
        生成调度触发策略
        year (int 或 str) 年，4位数字
        month (int 或 str) 月 (范围1-12)
        day (int 或 str) 日 (范围1-31
        week (int 或 str) 周 (范围1-53)
        day_of_week (int 或 str) 周内第几天或者星期几 (范围0-6 或者 mon,tue,wed,thu,fri,sat,sun)
        hour (int 或 str) 时 (范围0-23)
        minute (int 或 str) 分 (范围0-59)
        second (int 或 str) 秒 (范围0-59)
        start_date (datetime 或 str) 最早开始日期(包含)
        end_date (datetime 或 str) 最晚结束时间(包含)
        timezone (datetime.tzinfo 或str) 指定时区
        :param period:
        :return:
        '''
        crontab = task_obj.crontab
        crontab = crontab.replace("？", "*")
        crontab = crontab.replace("?", "*")
        cron_list = crontab.split(' ')
        # 兼容周几表达式
        try:
            week = cron_list[5]
            week_map = {
                '1': 'sun',
                '2': 'mon',
                '3': 'tue',
                '4': 'wed',
                '5': 'thu',
                '6': 'fri',
                '7': 'sat'
            }
            if week != '*':
                week_li = week.split(',')
                week_str = ','.join([week_map.get(i) for i in week_li])
                cron_list[5] = week_str
        except Exception as e:
            print(e)
        trigger = {
            'trigger': 'cron',
            'second': cron_list[0],
            'minute': cron_list[1],
            'hour': cron_list[2],
            'day': cron_list[3],
            'month': cron_list[4],
            'day_of_week': cron_list[5],
            'year': cron_list[6]
        }
        if task_obj.trigger_date:
            trigger_date = json.loads(task_obj.trigger_date)
            if trigger_date != []:
                trigger['start_date'] = trigger_date[0]
                if len(trigger_date) > 1:
                    trigger['end_date'] = trigger_date[1]
        return trigger

    def reset_all_job(self, req_dict):
        '''
        重启所有定时任务或拉起失败定时任务
        '''
        reset_all = req_dict.get('reset_all', 0)
        res = get_job_list({'pagesize': 99999})
        if res['code'] == 200:
            exist_job_list = res['data']['records']
        else:
            exist_job_list = []
        exist_job_ids = [i.get('id') for i in exist_job_list]
        task_obj_list = get_base_query(Task).filter(Task.trigger_type == 2).filter(Task.status == 1).all()
        for task_obj in task_obj_list:
            job_id = task_obj.id
            if reset_all or job_id not in exist_job_ids:
                res = self.start_task({'id': job_id})
                print(res)
        return gen_json_response(msg='操作成功！', extends={'success': True})

    def start_task(self, req_dict):
        '''
        开始任务
        '''
        task_id = req_dict.get('id')
        worker_queue = req_dict.get('worker_queue')
        trigger = req_dict.get('trigger', '')
        task_obj = get_base_query(Task).filter(Task.id == task_id).first()
        if task_obj is None:
            return gen_json_response(code=400, msg="未找到该任务!")
        job_id = task_id
        func_args = {
            'task_id': task_id
        }
        if task_obj.task_type == 1:
            # 普通任务调度参数
            func = 'normal_task'
        else:
            # dag 任务
            func = 'dag_task'
        if_exist = 'remove'
        if trigger == 'once':
            # 手动单次运行，不影响原有调度job
            trigger = {
                'trigger': 'once'
            }
            if_exist = 'pass'
        elif task_obj.trigger_type == 1:
            # 单次运行并删除调度job
            trigger = {
                'trigger': 'once'
            }
        else:
            trigger = self.gen_task_trigger(task_obj)
        req_dict = {
            'job_id': job_id,
            'func': func,
            'func_args': func_args,
            'run_type': 'celery',
            'trigger': trigger,
            'if_exist': if_exist,
            'worker_queue': worker_queue if worker_queue is not None else task_obj.run_queue,
            'priority': task_obj.priority
        }
        scheduler_res = add_job(req_dict)
        print(scheduler_res)
        return scheduler_res

    def get_obj_list(self, req_dict):
        '''
        获取列表
        '''
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        query = get_base_query(Task).filter(Task.task_type == 1)
        
        # 任务模版 查询逻辑
        template_code = req_dict.get('template_code', '')
        if template_code != '':
            query = query.filter(Task.template_code == template_code)
        # 名称 查询逻辑
        name = req_dict.get('name', '')
        if name != '':
            query = query.filter(Task.name.like("%" + name + "%"))
        query = query.order_by(Task.update_time.desc())
        total = query.count()
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_task_model(obj, ser_type='list')
            result.append(dic)
        res_data = {
            'records': result,
            'total': total
        }
        return gen_json_response(data=res_data)

    def get_dag_task_list(self, req_dict):
        '''
        获取dag任务列表
        '''
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        query = get_base_query(Task).filter(Task.task_type == 2)
        # 名称 查询逻辑
        name = req_dict.get('name', '')
        if name != '':
            query = query.filter(Task.name.like("%" + name + "%"))
        query = query.order_by(Task.update_time.desc())
        total = query.count()
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_task_model(obj, ser_type='list')
            result.append(dic)
        res_data = {
            'records': result,
            'total': total
        }
        return gen_json_response(data=res_data)

    def get_dag_task_menu(self, req_dict):
        '''
        获取dag任务模版菜单
        '''
        componentMap = {
            'name': 'componentTask',
            'title': '组件型任务',
            'children': []
        }
        dynamicMap = {
            'name': 'dynamicTask',
            'title': '配置型任务',
            'children': []
        }
        task_template_objs = get_base_query(TaskTemplate)
        for task_template_obj in task_template_objs:
            dic = {
                'id': task_template_obj.id,
                'img': task_template_obj.icon,
                'name': task_template_obj.name,
                'params': {
                    'template_code': task_template_obj.code,
                    'retry': 0,
                    'countdown': 0,
                    'error_type': 'throw',
                    'task_conf': {},
                },
            }
            if task_template_obj.type == 1:
                componentMap['children'].append(dic)
            else:
                dynamicMap['children'].append(dic)
        res_data = [componentMap, dynamicMap]
        print(res_data)
        return gen_json_response(data=res_data)

    def get_dag_task_node_status(self, req_dict):
        '''
        获取dag任务各节点状态
        '''
        task_id = req_dict.get('id')
        running_id = req_dict.get('running_id')
        if running_id in ['', None]:
            # 没有运行实例id，使用任务绑定的running_id
            task_obj = get_base_query(Task).filter(Task.id == task_id).first()
            running_id = task_obj.running_id
        child_instance_list = []
        task_info = None
        if running_id not in ['', None]:
            task_instance_obj = db.session.query(TaskInstance).filter(TaskInstance.id == running_id).first()
            if task_instance_obj:
                task_info = task_instance_obj.to_dict()
            child_instance_list = db.session.query(TaskInstance).filter(TaskInstance.task_id == task_id, TaskInstance.parent_id == running_id).all()
        data_list = []
        closed_list = []
        for task_instance in child_instance_list:
            dic = task_instance.to_dict()
            data_list.append(dic)
            if dic['closed'] == 1:
                closed_list.append(dic)
        is_ok = len(closed_list) == len(data_list)
        res_data = {
            'task_info': task_info,
            'child_list': data_list,
            'is_ok': is_ok
        }
        return gen_json_response(data=res_data)

    def get_task_template_params(self, req_dict):
        '''
        获取任务模版参数
        '''
        code = req_dict.get('code', '')
        template_obj = db.session.query(TaskTemplate).filter(TaskTemplate.code == code).first()
        if template_obj is None:
            return gen_json_response(code=400, msg='未找到对应任务模版')
        template_info = template_obj.to_dict()
        template_info['params'] = json.loads(template_info['params'])
        return gen_json_response(data=template_info)

    def get_obj_all_list(self, req_dict):
        '''
        获取全量列表
        '''
        query = get_base_query(Task)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_task_model(obj, ser_type='all_list')
            result.append(dic)
        return gen_json_response(data=result)
    
    def get_obj_detail(self, req_dict):
        '''
        获取详情
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(Task).filter(
            Task.id == obj_id,
            Task.del_flag == 0).first()
        if not obj:
            return gen_json_response(code=400, msg='未找到数据')
        dic = serialize_task_model(obj, ser_type='detail')
        return gen_json_response(data=dic)

    def get_obj_params_detail(self, req_dict):
        '''
        获取参数详情
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(Task).filter(
            Task.id == obj_id,
            Task.del_flag == 0).first()
        if not obj:
            return gen_json_response(code=400, msg='未找到数据')
        if obj.template_code:
            task_template_obj = db.session.query(TaskTemplate).filter(TaskTemplate.code == obj.template_code).first()
            template_info = task_template_obj.to_dict()
            template_info['params'] = json.loads(template_info['params'])
        else:
            template_info = None
        res_data = {
            'template_info': template_info,
            'params': json.loads(obj.params)
        }
        return gen_json_response(data=res_data)
    
    def add_obj(self, req_dict):
        '''
        添加
        '''
        obj = Task()
        for key in req_dict:
            if key in ['params']:
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            elif key == 'trigger_date':
                trigger_date = req_dict.get('trigger_date', '')
                if trigger_date is not None and ',' in trigger_date:
                    trigger_date = trigger_date.split(',')
                    setattr(obj, key, json.dumps(trigger_date, ensure_ascii=False, indent=2))
            else:
                setattr(obj, key, req_dict[key])
        obj.id = gen_uuid(res_type='base')
        set_insert_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        # 将任务加入调度
        if obj.status == 1:
            scheduler_res = self.start_task({'id': obj.id})
            print(scheduler_res)
        return gen_json_response(msg='添加成功', extends={'success': True})
    
    def edit_obj(self, req_dict):
        '''
        编辑
        '''
        obj_id = req_dict.get('id')
        is_scheduler = req_dict.get('is_scheduler', True)
        obj = db.session.query(Task).filter(Task.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        for key in req_dict:
            if key == 'params':
                if obj.task_type == 2:
                    flag, dag = gen_params_dag(req_dict[key])
                    if not flag:
                        return gen_json_response(code=400, msg='dag拓扑校验失败，请检查是否存在循环调用')
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            elif key == 'trigger_date':
                trigger_date = req_dict.get('trigger_date', '')
                if trigger_date is not None and ',' in trigger_date:
                    trigger_date = trigger_date.split(',')
                    setattr(obj, key, json.dumps(trigger_date, ensure_ascii=False, indent=2))
            else:
                setattr(obj, key, req_dict[key])
        set_update_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        if is_scheduler and obj.status == 1:
            # 将任务加入调度
            scheduler_res = self.start_task({'id': obj.id})
            if scheduler_res['code'] == 200:
                res_data = scheduler_res['data']
                return gen_json_response(data=res_data, msg='编辑成功', extends={'success': True})
            else:
                return scheduler_res
        else:
            return gen_json_response(msg='编辑成功', extends={'success': True})

    def edit_obj_status(self, req_dict):
        '''
        编辑状态
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(Task).filter(Task.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        obj.status = 1 if obj.status == 0 else 0
        set_update_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        # 添加或删除定时任务job
        if obj.status == 1:
            scheduler_res = self.start_task({'id': obj.id})
            print(scheduler_res)
        else:
            scheduler_res = remove_job([obj.id])
            print(scheduler_res)
        return gen_json_response(msg='操作成功', extends={'success': True})

    def delete_obj(self, req_dict):
        '''
        删除
        '''
        obj_id = req_dict['id']
        del_obj = db.session.query(Task).filter(Task.id == obj_id).first()
        if del_obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        del_obj.del_flag = 1
        set_update_user(del_obj)
        db.session.add(del_obj)
        db.session.commit()
        db.session.flush()
        scheduler_res = remove_job([obj_id])
        print(scheduler_res)
        return gen_json_response(code=200, msg='删除成功', extends={'success': True})
    
    def delete_batch(self, req_dict):
        '''
        批量删除
        '''
        del_ids = req_dict.get('ids')
        if isinstance(del_ids, str):
            del_ids = del_ids.split(',')
        del_objs = db.session.query(Task).filter(Task.id.in_(del_ids)).all()
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.commit()
            db.session.flush()
            scheduler_res = remove_job([del_obj.id])
            print(scheduler_res)
        return gen_json_response(code=200, msg='删除成功', extends={'success': True})
    
    def importExcel(self, file):
        '''
        excel导入
        '''
        try:
            df = pd.read_excel(file, dtype=object)
            df.fillna("", inplace=True)
            # 校验上传字段
            data_li = []
            n = 2
            for k, row in df.iterrows():
                row = row.to_dict()
                verify_dict = {}
                not_valid = validate_params(row, verify_dict)
                if not_valid:
                    not_valid = {
                        'code': 400,
                        'msg': f'第{n}行{not_valid}'
                    }
                    return not_valid
                data_li.append(row)
                n += 1
            
            # 循环导入
            for row in data_li:
                obj = Task()
                for key in row:
                    if key in ['params', 'trigger_date']:
                        setattr(obj, key, json.dumps(row[key], ensure_ascii=False, indent=2))
                    else:
                        setattr(obj, key, row[key])
                obj.id = gen_uuid(res_type='base')
                set_insert_user(obj)
                db.session.add(obj)
                db.session.commit()
                db.session.flush()
            return gen_json_response(code=200, msg='导入成功', extends={'success': True})
        except Exception as e:
            return gen_json_response(code=500, msg=f'导入错误{e}')
    
    
    def exportXls(self, req_dict):
        '''
        导出excel
        '''
        selections = req_dict.get('selections', '')
        ids = selections.split(',')
        obj_list = db.session.query(Task).filter(Task.id.in_(ids)).all()
        result = []
        for obj in obj_list:
            dic = serialize_task_model(obj, ser_type='export')
            result.append(dic)
        df = pd.DataFrame(result)
        print(df)
        # 使用字节流存储
        output = io.BytesIO()
        # 保存文件
        df.to_excel(output, index=False)
        # 文件seek位置，从头(0)开始
        output.seek(0)
        return output


if __name__ == '__main__':
    res = TaskApiService().get_instance_logs({"task_id": "e29ec2ae-89c3-4938-b13e-56c1a860cf46"})
    print(res)