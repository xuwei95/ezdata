import sys
sys.path.append('.')
from tasks.normal_task import normal_task
from tasks.dag_tasks import dag_task, dag_node_task
from tasks.data_tasks import self_gen_datasource_model, self_train_rag_data
from tasks.system_tasks import self_remove_task_history, self_scan_unclosed_tasks
from celery_app import celery_app

task_dict = {
    'normal_task': normal_task,
    'dag_task': dag_task,
    'dag_node_task': dag_node_task,
    'self_gen_datasource_model': self_gen_datasource_model,
    'self_remove_task_history': self_remove_task_history,
    'self_scan_unclosed_tasks': self_scan_unclosed_tasks,
    'self_train_rag_data': self_train_rag_data
}
