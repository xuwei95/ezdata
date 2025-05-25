from config import ES_CONF, SYS_LOG_INDEX, INTERFACE_LOG_INDEX
from utils.common_utils import gen_json_response, date_to_timestamp, get_now_time, format_date
from etl.libs.es import EsClient
from etl.utils.es_query_tool import EsQueryTool
from web_apps import db
from web_apps.task.db_models import TaskInstance
from web_apps.datamodel.db_models import DataModel
from sqlalchemy import func


class SysLogService(object):
    def __init__(self):
        pass

    def query_logs(self, req_dict):
        '''
        查询系统日志
        :param req_dict:
        :return:
        '''
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        es_client = EsClient(**ES_CONF)
        query_dict = {
            'index_name': SYS_LOG_INDEX,
            'sort[@timestamp]': 'desc',
            'page': page,
            'pagesize': pagesize
        }
        user_name = req_dict.get('user_name', '')
        if user_name != '':
            query_dict['contain[user_name]'] = user_name
        ip = req_dict.get('ip', '')
        if ip != '':
            query_dict['contain[ip]'] = ip
        api_path = req_dict.get('api_path', '')
        if api_path != '':
            query_dict['contain[api_path]'] = api_path
        levelname = req_dict.get('levelname', '')
        if levelname != '':
            query_dict['contain[levelname]'] = levelname
        time_range = req_dict.get('time_range', '')
        if time_range != '':
            t_li = time_range.split(',')
            query_dict['gte[@timestamp]'] = date_to_timestamp(t_li[0]) * 1000
            query_dict['lte[@timestamp]'] = date_to_timestamp(t_li[1]) * 1000
        print(query_dict)
        es_query_tool = EsQueryTool(query_dict)
        res_data = es_query_tool.query(es=es_client)
        return res_data


class SysInfoService(object):
    def __init__(self):
        pass

    def query_dashboard_count(self, req_dict):
        '''
        查询系统dashboard统计信息
        :param req_dict:
        :return:
        '''
        # 任务执行数统计
        now = get_now_time()
        today = format_date(now, format='%Y-%m-%d 00:00:00', res_type='datetime')
        today_ts = format_date(now, format='%Y-%m-%d 00:00:00', res_type='timestamp') - 3600 * 8
        task_count = db.session.query(TaskInstance).filter(TaskInstance.start_time >= today).count()
        model_count = db.session.query(DataModel).filter(DataModel.del_flag == 0).count()
        try:
            es_client = EsClient(**ES_CONF)
            visit_query_dict = {
                'index_name': SYS_LOG_INDEX,
                'gte[@timestamp]': today_ts * 1000,
                'pagesize': 0
            }
            es_query_tool = EsQueryTool(visit_query_dict)
            res_data = es_query_tool.query(es=es_client)
            if res_data.get('code') == 200:
                visit_count = res_data['data']['total']
            else:
                visit_count = 0
            interface_query_dict = {
                'index_name': INTERFACE_LOG_INDEX,
                'gte[@timestamp]': today_ts * 1000,
                'pagesize': 0
            }
            es_query_tool = EsQueryTool(interface_query_dict)
            res_data = es_query_tool.query(es=es_client)
            if res_data.get('code') == 200:
                interface_count = res_data['data']['total']
            else:
                interface_count = 0
        except Exception as e:
            print(f'es连接错误{e}')
            visit_count = 0
            interface_count = 0
        res_data = [
            {
                'title': '任务执行数',
                'icon': 'taREDACTEDcount|svg',
                'value': task_count,
                'color': 'green',
                'action': '今日',
            },
            {
                'title': '接口访问量',
                'icon': 'interface-count|svg',
                'value': interface_count,
                'color': 'blue',
                'action': '今日',
            },
            {
                'title': '系统访问量',
                'icon': 'visit-count|svg',
                'value': visit_count,
                'color': 'purple',
                'action': '今日',
            },
            {
                'title': '数据模型数',
                'icon': 'model-count|svg',
                'value': model_count,
                'color': 'orange',
                'action': '总数',
            },
        ]
        return gen_json_response(res_data)

    def query_visit_count(self, req_dict):
        '''
        查询接口调用统计
        :param req_dict:
        :return:
        '''
        es_client = EsClient(**ES_CONF)
        # 任务执行数统计
        now = get_now_time()
        end_time = format_date(now, format='%Y-%m-%d %H:00:00', res_type='timestamp') + 3600
        start_time = end_time - 86400
        query_body = {
            "query": {
                "bool": {
                    "must": [{
                        "range": {
                            "@timestamp": {
                                "gte": start_time * 1000,
                                "lte": end_time * 1000
                            }
                        }
                    }]
                }
            },
            "aggs": {
                "group_by_date": {
                    "date_histogram": {
                        "field": "@timestamp",
                        "interval": "hour",
                        "time_zone": "+08:00",
                        "format": "HH:00"
                    },
                }
            }
        }
        x_data = [format_date(start_time + 3600 * i, format='%H:00') for i in range(24)]
        res = es_client.query(SYS_LOG_INDEX, query_body)
        doc_count_map = {i['key_as_string']: i['doc_count'] for i in res['aggregations']['group_by_date']['buckets']}
        sys_line = [doc_count_map.get(i, 0) for i in x_data]
        try:
            res = es_client.query(INTERFACE_LOG_INDEX, query_body)
            doc_count_map = {i['key_as_string']: i['doc_count'] for i in res['aggregations']['group_by_date']['buckets']}
            interface_line = [doc_count_map.get(i, 0) for i in x_data]
        except Exception as e:
            print(e)
            interface_line = []
        res_data = {
            'x_data': x_data,
            'interface_line': interface_line,
            'sys_line': sys_line
        }
        return gen_json_response(res_data)

    def query_task_count(self, req_dict):
        '''
        查询任务执行统计
        :param req_dict:
        :return:
        '''
        # 任务执行数统计
        now = get_now_time()
        end_time = format_date(now, format='%Y-%m-%d %H:00:00', res_type='timestamp') + 3600
        start_time = end_time - 86400
        x_data = [format_date(start_time + 3600 * i, format='%H:00') for i in range(24)]
        task_count = db.session.query(func.date_format(TaskInstance.start_time, '%Y-%m-%d %H:00'), func.count('*').label('c')).filter(TaskInstance.start_time >= format_date(start_time)).group_by(func.date_format(TaskInstance.start_time, '%Y-%m-%d %H:00')).all()
        print(task_count)
        count_map = {i[0][-5:]: i[1] for i in task_count}
        task_line = [count_map.get(i, 0) for i in x_data]
        res_data = {
            'x_data': x_data,
            'task_line': task_line,
        }
        return gen_json_response(res_data)

    def query_interface_count(self, req_dict):
        '''
        查询数据接口统计
        :param req_dict:
        :return:
        '''
        es_client = EsClient(**ES_CONF)
        now = get_now_time()
        start_time = format_date(now, format='%Y-%m-%d 00:00:00', res_type='timestamp')
        query_body = {
            "query": {
                "bool": {
                    "must": [{
                        "range": {
                            "@timestamp": {
                                "gte": start_time * 1000,
                            }
                        }
                    }]
                }
            },
            "aggs": {
                "duration": {
                    "histogram": {
                       "field": "duration",
                       "interval": 0.1
                     }
                }
            }
        }
        res = es_client.query(SYS_LOG_INDEX, query_body)
        print(res)
        doc_count_map = {i['key']: i['doc_count'] for i in res['aggregations']['duration']['buckets']}
        res_data = [{
                'value': sum([v for k, v in doc_count_map.items() if k <= 0.1]),
                'name': '<0.1'
            }, {
                'value': sum([v for k, v in doc_count_map.items() if k > 0.1 and k <= 0.2]),
                'name': '0.1-0.2'
            }, {
                'value': sum([v for k, v in doc_count_map.items() if k > 0.2 and k <= 0.5]),
                'name': '0.2-0.5'
            }, {
                'value': sum([v for k, v in doc_count_map.items() if k > 0.5 and k <= 1]),
                'name': '0.5-1'
            }, {
                'value': sum([v for k, v in doc_count_map.items() if k >= 1]),
                'name': '>1'
            }
        ]
        return gen_json_response(res_data)

    def query_task_status_count(self, req_dict):
        '''
        查询任务状态统计
        :param req_dict:
        :return:
        '''
        now = get_now_time()
        today_time = format_date(now, format='%Y-%m-%d 00:00:00', res_type='timestamp')
        res_data = []
        status_group = db.session.query(TaskInstance.status, func.count('*').label('c')).filter(
            TaskInstance.start_time >= format_date(today_time)).group_by(TaskInstance.status).all()
        print(status_group)
        for i in status_group:
            res_data.append({'value': i[1], 'name': i[0]})
        return gen_json_response(res_data)

    def query_datamodel_type_count(self, req_dict):
        '''
        查询数据模型类型统计
        :param req_dict:
        :return:
        '''
        res_data = []
        model_group = db.session.query(DataModel.type, func.count('*').label('c')).filter(DataModel.del_flag == 0).group_by(DataModel.type).all()
        print(model_group)
        for i in model_group:
            res_data.append({'value': i[1], 'name': i[0]})
        return gen_json_response(res_data)


if __name__ == '__main__':
    req_dict = {
    }
    # SysLogService().query_logs(req_dict)
    # res = SysInfoService().query_dashboard_count(req_dict)
    # print(res)
    # res = SysInfoService().query_visit_count(req_dict)
    # print(res)
    # res = SysInfoService().query_task_count(req_dict)
    # print(res)
    res = SysInfoService().query_interface_count(req_dict)
    print(res)
