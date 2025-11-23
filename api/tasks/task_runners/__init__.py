from tasks.task_runners.py_tasks import PyTaskRunner
from tasks.task_runners.shell_tasks import ShellTaskRunner
from tasks.task_runners.spark_tasks import SparkTaskRunner
from tasks.task_runners.flink_tasks import FlinkTaskRunner
from tasks.task_runners.etl_tasks import EtlTaskRunner
from tasks.task_runners.dynamic_tasks import DynamicTaskRunner

runner_dict = {
    'PythonTask': PyTaskRunner,
    'ShellTask': ShellTaskRunner,
    'SparkTask': SparkTaskRunner,
    'FlinkTask': FlinkTaskRunner,
    'EtlTask': EtlTaskRunner,
}
