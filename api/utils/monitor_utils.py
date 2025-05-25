'''
服务器监控相关api
'''
import time
import datetime
import psutil
import os


def get_monitor_info():
    '''
    获取监控信息
    '''
    # cpu 信息
    cpu_precent = psutil.cpu_percent(1)
    cpu_precent = round(cpu_precent / 100, 4)
    # 内存信息
    phymem = psutil.virtual_memory()
    mem_total = round(phymem.total / 1024 / 1024 / 1024, 2)
    mem_used = round(phymem.used / 1024 / 1024 / 1024, 2)
    mem_precent = round(mem_used / mem_total, 4)
    # 磁盘信息
    statvfs = os.statvfs('/')
    disk_total = statvfs.f_frsize * statvfs.f_blocks
    disk_free = statvfs.f_frsize * statvfs.f_bfree
    disk_used = disk_total - disk_free
    disk_percent = round(disk_used / disk_total, 4)
    disk_used = round(disk_used / 1024 / 1024 / 1024, 2)
    disk_total = round(disk_total / 1024 / 1024 / 1024, 2)
    # 网络信息
    network_sent = int(psutil.net_io_counters()[0] / 1024)
    network_recv = int(psutil.net_io_counters()[1] / 1024)
    time.sleep(1)
    network_sent2 = int(psutil.net_io_counters()[0] / 1024)
    network_recv2 = int(psutil.net_io_counters()[1] / 1024)
    net_sent = network_sent2 - network_sent
    net_recv = network_recv2 - network_recv
    # 采集时间
    monitor_time = str(datetime.datetime.now())[:19]
    dic = {
        'time': monitor_time,
        'cpu_precent': cpu_precent,
        'mem_used': mem_used,
        'mem_total': mem_total,
        'mem_precent': mem_precent,
        'disk_used': disk_used,
        'disk_total': disk_total,
        'disk_percent': disk_percent,
        'net_sent': net_sent,
        'net_recv': net_recv
    }
    return dic


if __name__ == '__main__':
    dic = get_monitor_info()
    print(dic)


