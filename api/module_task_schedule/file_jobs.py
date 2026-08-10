"""文件管理后台维护任务(供 APScheduler sys_job 调度)。

移植自 RuoYi-Vue3-FastAPI 的 module_task/file_task.py,适配 ezdata:
- 均为系统级全库扫描(保留提醒/回收站清理/存储对账),用 tenant_bypass 绕过租户过滤,
  否则只扫到当前(常为空)租户。
- 无必需入参(SchedulerUtil._import_function 只按 module.func 导入,不解析实参),
  阈值走默认值;需自定义可改此处默认或后续扩展参数解析。
- sys_job.invoke_target 指向本模块函数,如:
    module_task_schedule.file_jobs.scan_retention_reminders
    module_task_schedule.file_jobs.purge_recycle_bin
    module_task_schedule.file_jobs.reconcile_file_storage
"""

from common.context import tenant_bypass
from config.database import AsyncSessionLocal
from module_admin.service.file_business_service import FileRetentionNoticeService
from module_admin.service.file_service import FileLifecycleService, FileReconcileService
from utils.log_util import logger

MAX_TASK_BATCHES = 100


async def scan_retention_reminders(remind_days: int = 7, batch_size: int = 500) -> None:
    """扫描文件保留期限并生成提醒(系统级,跨租户)。"""
    expiring_count = 0
    expired_count = 0
    with tenant_bypass():
        async with AsyncSessionLocal() as query_db:
            for _ in range(MAX_TASK_BATCHES):
                scan_result = await FileRetentionNoticeService.scan_file_retention_notices_services(
                    query_db, remind_days=remind_days, batch_size=batch_size
                )
                expiring_count += scan_result.expiring_count
                expired_count += scan_result.expired_count
                if scan_result.expiring_count < batch_size and scan_result.expired_count < batch_size:
                    break
            else:
                logger.warning('文件保留期限提醒扫描达到最大批次数，请检查待处理文件数量')
    logger.info(f'文件保留期限提醒扫描完成，即将到期{expiring_count}个，已到期{expired_count}个')


async def purge_recycle_bin(retention_days: int = 30, batch_size: int = 100) -> None:
    """永久清理超过保留期限的回收站文件(系统级,跨租户)。"""
    purge_count = 0
    with tenant_bypass():
        async with AsyncSessionLocal() as query_db:
            for _ in range(MAX_TASK_BATCHES):
                current_count = await FileLifecycleService.purge_recycle_bin_services(
                    query_db, retention_days=retention_days, batch_size=batch_size
                )
                purge_count += current_count
                if current_count < batch_size:
                    break
            else:
                logger.warning('回收站永久清理达到最大批次数，请检查待处理文件数量')
    logger.info(f'回收站永久清理完成，共清理{purge_count}个文件')


async def reconcile_file_storage(check_hash: bool = False) -> None:
    """执行数据库和本地文件系统双向对账(系统级;内部取全量已 tenant_bypass)。"""
    with tenant_bypass():
        await FileReconcileService.run_scheduled_reconcile_services(check_hash)
