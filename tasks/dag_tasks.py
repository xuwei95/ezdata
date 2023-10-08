'''
dag任务
'''
from celery_app import celery_app, MyTask
from web_apps.task.db_models import Task, TaskTemplate, TaskInstance
from web_apps import db
from utils.task_util import get_task_instance, update_task_instance, set_task_instance_running, set_task_instance_failed, set_task_instance_retry
from utils.log_utils import get_task_logger
from utils.common_utils import gen_uuid, get_now_time
from utils.dag import DAG
from celery import group, signature
import json
from tasks.task_runners import runner_dict, DynamicTaskRunner
from web_apps.alert.strategys.task_alert_strategys import handle_task_fail_alert


class CeleryDag(object):
    def __init__(self, dag, task_id, uuid, run_queue):
        '''
        celery 任务dag调度
        '''
        self.dag = dag
        self.task_id = task_id
        self.uuid = uuid
        self.run_queue = run_queue
        self.sorted_nodes = self.dag.topological_sort()
        self.al_schedule_nodes = []

    def gen_node_task(self, node):
        '''
        生成节点任务
        '''
        return signature(dag_node_task.si(node, self.task_id, self.uuid), queue=self.run_queue)

    def gen_task_link(self, task_list):
        '''
        生成任务调用链
        '''
        task = task_list[0]
        for t in task_list[1:]:
            task = (task | t)
        return task

    def schedule_node(self, node):
        '''
        调度节点
        '''
        # 生成当前节点任务
        task = self.gen_node_task(node)
        # 将节点加入已调度节点
        self.al_schedule_nodes.append(node)
        # 获取节点下游任务节点列表
        down_nodes = self.dag.downstream(node)
        # 找到下游节点中前置节点只有该节点的下游任务节点，生成组合调用链
        single_down_nodes = [down_node for down_node in down_nodes if self.dag.predecessors(down_node) == [node]]
        if single_down_nodes != []:
            single_down_group_task = group([self.schedule_node(down_node) for down_node in single_down_nodes])
            task = self.gen_task_link([task, single_down_group_task])
        return task

    def start(self):
        '''
        开始执行，从根节点启动dag任务
        '''
        # 找到无前置节点的任务
        ind_nodes = self.dag.ind_nodes()
        # 组合调度
        all_tasks = []
        task_list = [self.schedule_node(node) for node in ind_nodes]
        task = group(task_list)
        all_tasks.append(task)
        # 找到父节点都已被调度的所有未调度节点，循环组合调度，直到所有节点均被调度
        while len(self.al_schedule_nodes) != len(self.sorted_nodes):
            group_task_nodes = [i for i in self.sorted_nodes if i not in self.al_schedule_nodes and [n for n in self.dag.predecessors(i) if n not in self.al_schedule_nodes] == []]
            group_task = group([self.schedule_node(node) for node in group_task_nodes])
            all_tasks.append(group_task)
        run_task = self.gen_task_link(all_tasks)
        res = run_task()
        print(res)

    def run_all(self):
        '''
        按dag拓扑顺序执行各节点任务
        '''
        for node in self.sorted_nodes:
            dag_node_task(node, self.task_id, self.uuid)


def gen_params_dag(params):
    '''
    根据任务参数生成dag
    '''
    cells = params.get('cells', [])
    nodes = [i['id'] for i in cells if i['shape'] == 'container-node']
    links = [{'source': i['source']['cell'], 'target': i['target']['cell']} for i in cells if
             i['shape'] == 'edge']
    dag = DAG()
    try:
        for node in nodes:
            dag.add_node(node)
        for link in links:
            dag.add_edge(link['source'], link['target'])
        dag.topological_sort()
    except Exception as e:
        return False, str(e)
    return True, dag


@celery_app.task(base=MyTask, once={'graceful': True}, bind=True)
def dag_node_task(self, node_id, task_id, parent_uuid):
    '''
    dag节点任务
    '''
    uuid = self.request.id if self.request.id else gen_uuid()
    logger = get_task_logger(p_name='normal_task',task_log_keys={'task_uuid': uuid})
    worker = self.request.hostname if self.request.hostname else ''
    logger.info(f'任务开始，任务id:{uuid}, 执行worker:{worker}')
    try:
        task_instance_obj = get_task_instance(uuid, task_id, {'node_id': node_id, 'parent_id': parent_uuid, 'worker': worker})
    except Exception as e:
        logger.exception(f"任务实例记录创建失败")
        raise e
    task_obj = db.session.query(Task).filter(Task.id == task_id).first()
    if task_obj is None or task_obj.del_flag == 1:
        set_task_instance_failed(task_instance_obj, '任务未找到或已被删除')
        return
    retry = 0
    countdown = 0
    error_type = 'break'
    task_info = {}
    try:
        task_params = json.loads(task_obj.params)
        node_task = [i for i in task_params.get('cells', []) if i['id'] == node_id]
        if node_task != []:
            node_task = node_task[0]
            task_info = node_task['data']['params']
            task_info['name'] = node_task['data']['label']
            set_task_instance_running(task_instance_obj, task_obj, {'progress': 0})
            template_code = task_info.get('template_code')
            task_conf = task_info.get('task_conf', {})
            retry = task_info.get('retry', 0)
            countdown = task_info.get('countdown', 0)
            error_type = task_info.get('error_type', 'break')
            task_template_obj = db.session.query(TaskTemplate).filter(
                TaskTemplate.code == template_code, TaskTemplate.del_flag == 0).first()
            runner_type = task_template_obj.runner_type
            if runner_type == 1:
                Runner = runner_dict.get(template_code)
                if Runner is None:
                    raise ValueError(f'处理失败:未找到任务执行器')
                else:
                    task_runner = Runner(params=task_conf, logger=logger)
            else:
                runner_code = task_template_obj.runner_code
                task_runner = DynamicTaskRunner(params=task_conf, logger=logger, runner_code=runner_code)
            task_runner.run()
            update_task_instance(task_instance_obj,
                                 {'status': 'success', 'progress': 100, 'closed': 1, 'result': '成功',
                                  'end_time': get_now_time('datetime')})
    except Exception as e:
        logger.exception(e)
        set_task_instance_failed(task_instance_obj, f'处理失败:{str(e)[:1000]}')
        retries = self.request.retries
        print('retry', retries)
        if retries < retry:
            logger.info(f'任务出错，第{retries + 1}次重试')
            set_task_instance_retry(task_instance_obj, retries + 1)
            self.retry(exc=e, countdown=countdown, max_retries=retry)
        else:
            alert_conf = {
                'alert_strategy_ids': task_obj.alert_strategy_ids,
                'task_uuid': uuid,
                'worker': worker,
                'retries': retries,
                'exception': str(e),
                'exception_line': str(e.__traceback__.tb_lineno),
                'exception_file': e.__traceback__.tb_frame.f_globals["__file__"],
                'type': 'dag_node_task',
                'task_info': task_info
            }
            handle_task_fail_alert(alert_conf)
            if error_type != 'break':
                raise e


@celery_app.task(bind=True)
def dag_task(self, task_id):
    '''
    dag任务调度
    :return:
    '''
    uuid = self.request.id if self.request.id else gen_uuid()
    worker = self.request.hostname if self.request.hostname else ''
    logger = get_task_logger(p_name='dag_task', task_log_keys={'task_uuid': uuid})
    logger.info(f'任务开始，任务id:{uuid}, 执行worker:{worker}')
    task_instance_obj = get_task_instance(uuid, task_id, {'worker': worker})
    task_obj = db.session.query(Task).filter(Task.id == task_id).first()
    if task_obj is None or task_obj.del_flag == 1:
        set_task_instance_failed(task_instance_obj, '任务未找到或已被删除')
        return
    retry = task_obj.retry
    countdown = task_obj.countdown
    try:
        logger.info(f'任务：{task_obj.name}开始执行')
        params = json.loads(task_obj.params)
        set_task_instance_running(task_instance_obj, task_obj, {'progress': 0})
        flag, dag = gen_params_dag(params)
        if not flag:
            set_task_instance_failed(task_instance_obj, f"处理失败：{str(dag)[:1000]}")
        run_queue = task_obj.run_queue
        task_dag = CeleryDag(dag, task_id, uuid, run_queue)
        run_type = task_obj.run_type  # dag运行类型，1分布式2，单进程
        if run_type == 1:
            # 分布式运行各节点任务
            task_dag.start()
        elif run_type == 2:
            # 单进程顺序运行各节点任务
            task_dag.run_all()
        logger.info(f'任务：{task_obj.name}调度成功')
        # # 定时扫描节点任务状态，更新进度
        # cells = params.get('cells', [])
        # dag_nodes = [i['id'] for i in cells if i['shape'] == 'container-node']
        # flag = True
        # while flag:
        #     complete_node_tasks = db.session.query(TaskInstance).filter(TaskInstance.parent_id == uuid, TaskInstance.closed == 1).all()
        #     if len(complete_node_tasks) == len(dag_nodes):
        #         flag = False
        #         update_task_instance(task_instance_obj,
        #                              {'status': 'success', 'progress': 100, 'closed': 1, 'result': '成功', 'end_time': get_now_time('datetime')})
        #     else:
        #         process_num = len(complete_node_tasks)
        #         update_task_instance(task_instance_obj, {'progress': (process_num / len(dag_nodes)) * 100})
        #         logger.info(f'已完成节点任务数：{process_num}， 总节点任务数：{len(dag_nodes)}')
        #     time.sleep(10)
        update_task_instance(task_instance_obj, {'status': 'success', 'progress': 100, 'closed': 1, 'result': '成功', 'end_time': get_now_time('datetime')})
    except Exception as e:
        logger.exception(e)
        set_task_instance_failed(task_instance_obj, f'处理失败:{str(e)[:1000]}')
        retries = self.request.retries
        print('retry', retries)
        if retries < retry:
            logger.info(f'任务出错，第{retries + 1}次重试')
            set_task_instance_retry(task_instance_obj, retries + 1)
            self.retry(exc=e, countdown=countdown, max_retries=retry)
        else:
            alert_conf = {
                'alert_strategy_ids': task_obj.alert_strategy_ids,
                'task_uuid': uuid,
                'worker': worker,
                'retries': retries,
                'exception': str(e),
                'exception_line': str(e.__traceback__.tb_lineno),
                'exception_file': e.__traceback__.tb_frame.f_globals["__file__"],
                'type': 'dag_task',
                'task_info': task_obj.to_dict()
            }
            handle_task_fail_alert(alert_conf)
            raise e


if __name__ == '__main__':
    # dag_task('fdacfa5b336b47aeba93376d9e5a4621')
    dag_node_task('4f9fe00b-5f91-477b-ba5d-eb8370de23cd', 'fdacfa5b336b47aeba93376d9e5a4621', '084f343b-7c32-40db-819e-2c55a1ee5c62')

