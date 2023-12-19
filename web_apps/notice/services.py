# coding: utf-8
'''
通知公告服务
'''
import datetime
import json

from web_apps import db
from utils.query_utils import get_base_query
from utils.auth import set_insert_user, set_update_user, get_auth_token_info
from utils.common_utils import gen_json_response, timestamp_to_date, date_to_timestamp, get_now_time, format_date
from models import Notice, NoticeSend, User
from sqlalchemy import or_


def serialize_notice(obj, ser_type='list'):
    '''
    序列化通知数据
    :param obj:
    :param ser_type:
    :return:
    '''
    dic = {}
    if ser_type == 'list':
        dic = obj.to_dict()
        for k in ['start_time', 'end_time', 'send_time', 'cancel_time']:
            dic[k] = timestamp_to_date(getattr(obj, k))
        for k in ['create_time', 'update_time']:
            dic[k] = str(getattr(obj, k))
        dic['user_ids'] = json.loads(obj.user_ids)
    if ser_type == 'send':
        notice_id = obj.notice_id
        notice_obj = db.session.query(Notice).filter(Notice.id == notice_id).first()
        if notice_obj:
            dic = notice_obj.to_dict()
            for k in ['start_time', 'end_time', 'send_time', 'cancel_time']:
                dic[k] = timestamp_to_date(getattr(notice_obj, k))
            for k in ['create_time', 'update_time']:
                dic[k] = str(getattr(notice_obj, k))
            dic['user_ids'] = json.loads(notice_obj.user_ids)
            dic['send_id'] = obj.id
            dic['read_flag'] = obj.read_flag
            dic['star_flag'] = str(obj.star_flag)
    return dic


class NoticeService(object):
    def __init__(self):
        pass

    def get_obj_list(self, req_dict):
        '''
        获取列表
        '''
        page = req_dict.get('page', 1)
        pagesize = req_dict.get('pagesize', 10)
        query = get_base_query(Notice)
        #  search_text 查询逻辑
        search_text = req_dict.get('search_text', '')
        if search_text != '':
            search_text = f"%{search_text}%"
            print(search_text)
            query = query.filter(or_(Notice.title.like(search_text), Notice.value.like(search_text)))
        total = query.count()
        page = int(page)
        pagesize = int(pagesize)
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_notice(obj, ser_type='list')
            result.append(dic)
        res_data = {
            'records': result,
            'total': total
        }
        return gen_json_response(data=res_data)

    def get_obj_list_by_user(self, req_dict):
        '''
        获取用户通知列表
        :param req_dict:
        :return:
        '''
        user_info = get_auth_token_info()
        user_id = user_info.get('userId')
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        query = get_base_query(NoticeSend).filter(NoticeSend.user_id == user_id)
        starFlag = req_dict.get('starFlag', '')
        if starFlag != '':
            query = query.filter(NoticeSend.star_flag == 1)
        rangeDateKey = req_dict.get('rangeDateKey', '')
        if rangeDateKey != '':
            now = get_now_time()
            today = format_date(now, format='%Y-%m-%d 00:00:00', res_type='timestamp')
            today_date = format_date(today, res_type='datetime')
            to_week = format_date(today_date + datetime.timedelta(days=0 - today_date.weekday()), res_type='timestamp')
            to_month = format_date(now, format='%Y-%m-01 00:00:00', res_type='timestamp')
            rangeDateMap = {
                'jt': [today, now],  # 今天
                'zt': [today - 86400, today],  # 昨天
                'qt': [today - 86400 * 2, today - 86400],  # 前天
                'bz': [to_week, now],  # 本周
                'sz': [to_week - 86400 * 7, to_week],  # 上周
                'by': [to_month, now],  # 本月
                'sy': [to_month - 86400 * 30, to_month],  # 上月
            }
            if rangeDateKey == 'zdy':
                beginDate = format_date(req_dict.get('beginDate'), res_type='datetime')
                endDate = format_date(req_dict.get('endDate'), res_type='datetime')
            else:
                beginDate = format_date(rangeDateMap.get(rangeDateKey)[0], res_type='datetime')
                endDate = format_date(rangeDateMap.get(rangeDateKey)[1], res_type='datetime')
            query = query.filter(NoticeSend.create_time >= beginDate).filter(NoticeSend.create_time <= endDate)
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_notice(obj, ser_type='send')
            result.append(dic)
        return gen_json_response(data=result)

    def add_obj(self, req_dict):
        '''
        添加
        '''
        obj = Notice()
        for k in req_dict:
            setattr(obj, k, req_dict[k])
        for k in ['start_time', 'end_time', 'send_time', 'cancel_time']:
            if k in req_dict:
                setattr(obj, k, date_to_timestamp(req_dict[k]))
        if 'user_ids' in req_dict:
            obj.user_ids = json.dumps(req_dict.get('user_ids').split(','))
        set_insert_user(obj)
        obj.sender = obj.create_by
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        NoticeSendService().handle_notice(obj)
        return gen_json_response(msg='添加成功。', extends={'success': True})
    
    def update_obj(self, req_dict):
        '''
        修改
        '''
        return gen_json_response(msg='修改成功。', extends={'success': True})
    
    def delete_obj(self, req_dict):
        '''
        删除
        '''
        if 'id' in req_dict:
            del_ids = [req_dict['id']]
        elif 'ids' in req_dict:
            del_ids = req_dict['ids']
        else:
            del_ids = req_dict
        del_objs = db.session.query(Notice).filter(Notice.id.in_(del_ids)).all()
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.commit()
            db.session.flush()
        return gen_json_response(msg='删除成功。')


class NoticeSendService(object):
    def __init__(self):
        pass

    def get_obj_list(self, req_dict):
        '''
        获取列表
        '''
        page = req_dict.get('page', 1)
        pagesize = req_dict.get('pagesize', 10)
        query = get_base_query(Notice)
        #  search_text 查询逻辑
        search_text = req_dict.get('search_text', '')
        if search_text != '':
            search_text = f"%{search_text}%"
            print(search_text)
            query = query.filter(or_(Notice.title.like(search_text), Notice.value.like(search_text)))
        total = query.count()
        page = int(page)
        pagesize = int(pagesize)
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_notice(obj, ser_type='list')
            result.append(dic)
        res_data = {
            'records': result,
            'total': total
        }
        return gen_json_response(data=res_data)

    def update_obj(self, req_dict):
        '''
        修改
        :param req_dict:
        :return:
        '''
        send_id = req_dict.get('send_id')
        print(send_id)
        obj = db.session.query(NoticeSend).filter(NoticeSend.id == send_id).first()
        print(obj)
        if obj is None:
            return gen_json_response(msg='找不到该对象！')
        if 'star_flag' in req_dict:
            obj.star_flag = req_dict.get('star_flag')
        if 'read_flag' in req_dict:
            obj.read_flag = req_dict.get('read_flag')
        set_update_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='更新成功!')

    def handle_notice(self, notice_obj, is_sys=False):
        '''
        解析通知，发送通知信息
        '''
        if isinstance(notice_obj, int):
            notice_obj = db.session.query(Notice).filter(Notice.id == notice_obj).first()
        msg_type = notice_obj.msg_type
        if msg_type == 'ALL':
            user_objs = get_base_query(User).all()
            user_ids = [i.id for i in user_objs]
        else:
            user_ids = json.loads(notice_obj.user_ids)
        notice_id = notice_obj.id
        for user_id in user_ids:
            send_obj = NoticeSend(
                notice_id=notice_id,
                user_id=user_id
            )
            if is_sys:
                send_obj.create_by = 'system'
            else:
                set_insert_user(send_obj)
            db.session.add(send_obj)
            db.session.commit()
            db.session.flush()
            print(f'send notice:{notice_id}, {user_id}')
        notice_obj.send_status = 1
        notice_obj.send_time = get_now_time()
        if is_sys:
            notice_obj.update_by = 'system'
        else:
            set_update_user(notice_obj)
        db.session.add(notice_obj)
        db.session.commit()
        db.session.flush()


if __name__ == '__main__':
    # obj = db.session.query(NoticeSend).filter(NoticeSend.id == 11).first()
    # print(obj)
    now = get_now_time()
    today = format_date(now, format='%Y-%m-%d 00:00:00', res_type='timestamp')
    today_date = format_date(today, res_type='datetime')
    to_week = format_date(today_date + datetime.timedelta(days=0 - today_date.weekday()), res_type='timestamp')
    to_month = format_date(now, format='%Y-%m-01 00:00:00', res_type='timestamp')
    rangeDateMap = {
        'jt': today,  # 今天
        'zt': today - 86400,  # 昨天
        'qt': today - 86400 * 2,  # 前天
        'bz': to_week,  # 本周
        'sz': to_week - 86400 * 7,  # 上周
        'by': to_month,  # 本月
        'sy': to_month - 86400 * 30,  # 上月
    }
    for k in rangeDateMap:
        print(k, format_date(rangeDateMap[k], res_type='datetime'))
