import pytest
from playwright.async_api import async_playwright

from common.base_page_test import BasePageTest
from common.config import Config


class AlertRecordManagementTest(BasePageTest):
    """告警记录管理测试

    测试环境无 Celery worker，告警记录可能为空，故主要验证页面加载与查询过滤可用；
    若存在记录则验证「处理」操作。
    """

    async def test_record_page(self) -> None:
        await self.goto_page(Config.frontend_url + '/alert/record')
        await self.wait_for_selector('text=标题')

        # 状态过滤可用
        form = self.page.locator('form').first
        await form.locator('.el-select').first.click()
        await self.page.get_by_role('option', name='未处理').click()
        await self.page.get_by_role('button', name='搜索').click()
        await self.page.wait_for_timeout(1000)

        # 表格存在(可能 0 行)
        await self.wait_for_selector('table', timeout=10000)

        # 若有记录，验证「处理」流程
        rows = await self.page.locator('tbody tr').count()
        if rows > 0:
            first_row = self.page.locator('tbody tr').first
            process_btn = first_row.get_by_role('button', name='处理')
            if await process_btn.count() > 0:
                await process_btn.click()
                await self.page.get_by_role('button', name='确定').click()
                await self.wait_for_selector("div:has-text('操作成功')", timeout=10000)


@pytest.mark.asyncio
async def test_alert_record_management_page() -> None:
    """测试告警记录管理页面"""
    async with async_playwright() as p:
        test_instance = AlertRecordManagementTest()
        await test_instance.setup(p)
        try:
            await test_instance.test_record_page()
        finally:
            await test_instance.teardown()
