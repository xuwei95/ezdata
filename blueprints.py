'''
web app注册字典
'''
from config import SYS_CONF

BLUEPRINT_DICT = {
    'sys': {
        'blueprint': 'web_apps.system.views.system_views.system_bp',
        'url_prefix': '/api/sys'
    },
    'user': {
        'blueprint': 'web_apps.system.views.user_views.user_bp',
        'url_prefix': '/api/sys/user'
    },
    'permission': {
        'blueprint': 'web_apps.system.views.permission_views.permission_bp',
        'url_prefix': '/api/sys/permission'
    },
    'role': {
        'blueprint': 'web_apps.system.views.role_views.role_bp',
        'url_prefix': '/api/sys/role'
    },
    'depart': {
        'blueprint': 'web_apps.system.views.depart_views.depart_bp',
        'url_prefix': '/api/sys/sysDepart'
    },
    'position': {
        'blueprint': 'web_apps.system.views.position_views.position_bp',
        'url_prefix': '/api/sys/position'
    },
    'tenant': {
        'blueprint': 'web_apps.system.views.tenant_views.tenant_bp',
        'url_prefix': '/api/sys/tenant'
    },
    'dict': {
        'blueprint': 'web_apps.dictionary.views.dict_bp',
        'url_prefix': '/api/sys/dict'
    },
    'file': {
        'blueprint': 'web_apps.ossfile.views.file_bp',
        'url_prefix': '/api/sys/oss/file'
    },
    'notice': {
        'blueprint': 'web_apps.notice.views.notice_bp',
        'url_prefix': '/api/sys/notice'
    },
    'screen': {
        'blueprint': 'web_apps.bigscreen.views.screen_bp',
        'url_prefix': '/api/screen'
    },
    'code_generator': {
        'blueprint': 'web_apps.code_generator.views.code_gen_bp',
        'url_prefix': '/api/code_generator'
    },
    'datasource': {
        'blueprint': 'web_apps.datasource.views.datasource_bp',
        'url_prefix': '/api/datasource'
    },
    'datamodel': {
        'blueprint': 'web_apps.datamodel.views.datamodel_bp',
        'url_prefix': '/api/datamodel'
    },
    'datamodel_field': {
        'blueprint': 'web_apps.datamodel.field_views.datamodel_field_bp',
        'url_prefix': '/api/datamodel/field'
    },
    'data_interface': {
        'blueprint': 'web_apps.datamodel.interface_views.data_interface_bp',
        'url_prefix': '/api/data_interface'
    },
    'task_template': {
        'blueprint': 'web_apps.task.task_template_views.task_template_bp',
        'url_prefix': '/api/task_template'
    },
    'task': {
        'blueprint': 'web_apps.task.views.task_bp',
        'url_prefix': '/api/task'
    },
    'algorithm': {
        'blueprint': 'web_apps.algorithm.views.algorithm_bp',
        'url_prefix': '/api/algorithm'
    },
    'alert': {
        'blueprint': 'web_apps.alert.views.alert_bp',
        'url_prefix': '/api/alert'
    },
    'alert_strategy': {
        'blueprint': 'web_apps.alert.strategy_views.alert_strategy_bp',
        'url_prefix': '/api/alert_strategy'
    },
    'rag_dataset': {
        'blueprint': 'web_apps.rag.views.dataset_views.dataset_bp',
        'url_prefix': '/api/rag/dataset'
    },
    'rag_document': {
        'blueprint': 'web_apps.rag.views.document_views.document_bp',
        'url_prefix': '/api/rag/document'
    },
    'rag_chunk': {
        'blueprint': 'web_apps.rag.views.chunk_views.chunk_bp',
        'url_prefix': '/api/rag/chunk'
    },
}
# 根据是否开启llm模块，添加llm模块
if SYS_CONF.get('LLM_TYPE'):
    BLUEPRINT_DICT['llm'] = {
        'blueprint': 'web_apps.llm.views.llm_bp',
        'url_prefix': '/api/llm'
    }
