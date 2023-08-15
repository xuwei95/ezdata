import sys
sys.path.append('.')
from tasks.normal_task import normal_task
from tasks.dag_tasks import dag_task, dag_node_task
from celery_app import celery_app

task_dict = {
    'normal_task': normal_task,
    'dag_task': dag_task,
    'dag_node_task': dag_node_task
}
