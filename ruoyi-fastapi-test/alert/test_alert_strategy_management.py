from datetime import datetime

import pytest
from playwright.async_api import async_playwright

from common.base_page_test import BasePageTest
from common.config import Config


class AlertStrategyManagementTest(BasePageTest):
    """告警策略管理测试(webhook/kafka/email 渠道配置)"""

    def generate_strategy_data(self) -> dict:
        timestamp = datetime.now().strftime('%H%M%S')
        return {
            'name': f'测试策略_{timestamp}',
            'webhook_url': 'http://localhost:9099/dev-api/alert/test-sink',
            'name_edit': f'测试策略_{timestamp}_edit',
        }

    async def create_strategy(self, name: str, webhook_url: str) -> None:
        """新增策略：名称 + 等级 + webhook 渠道"""
        await self.page.get_by_role('button', name='新增').click()
        dialog = self.page.get_by_role('dialog')
        await dialog.wait_for()

        await dialog.get_by_role('textbox', name='策略名称').fill(name)

        # 新增对话框默认带一个 webhook 渠道，填写 URL
        await dialog.get_by_placeholder('Webhook 地址 URL').fill(webhook_url)

        await dialog.get_by_role('button', name='确 定').click()
        await self.wait_for_selector("div:has-text('新增成功')", timeout=10000)

    async def search_strategy(self, name: str) -> None:
        form = self.page.locator('form').first
        await form.get_by_role('textbox', name='策略名称').fill(name)
        await self.page.get_by_role('button', name='搜索').click()
        await self.page.wait_for_timeout(1000)

    async def edit_strategy(self, name: str, new_name: str) -> None:
        await self.search_strategy(name)
        row = self.page.locator('tbody tr').first
        await row.get_by_role('button', name='修改').click()
        dialog = self.page.get_by_role('dialog')
        await dialog.wait_for()
        await dialog.get_by_role('textbox', name='策略名称').fill(new_name)
        await dialog.get_by_role('button', name='确 定').click()
        await self.wait_for_selector("div:has-text('修改成功')", timeout=10000)

    async def delete_strategy(self, name: str) -> None:
        await self.search_strategy(name)
        row = self.page.locator('tbody tr').first
        await row.get_by_role('button', name='删除').click()
        await self.page.get_by_role('button', name='确定').click()
        await self.wait_for_selector("div:has-text('删除成功')", timeout=10000)

    async def test_strategy_crud_operations(self) -> None:
        data = self.generate_strategy_data()

        await self.goto_page(Config.frontend_url + '/alert/strategy')
        await self.wait_for_selector('text=策略名称')

        await self.create_strategy(data['name'], data['webhook_url'])
        await self.edit_strategy(data['name'], data['name_edit'])
        await self.delete_strategy(data['name_edit'])


@pytest.mark.asyncio
async def test_alert_strategy_management_page() -> None:
    """测试告警策略管理页面"""
    async with async_playwright() as p:
        test_instance = AlertStrategyManagementTest()
        await test_instance.setup(p)
        try:
            await test_instance.test_strategy_crud_operations()
        finally:
            await test_instance.teardown()
