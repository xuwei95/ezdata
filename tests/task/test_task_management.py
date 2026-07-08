from datetime import datetime

import pytest
from playwright.async_api import async_playwright

from common.base_page_test import BasePageTest
from common.config import Config


class TaskManagementTest(BasePageTest):
    """任务管理测试(模板驱动低代码表单 + 执行 + 执行记录抽屉)"""

    def generate_task_data(self) -> dict:
        timestamp = datetime.now().strftime('%H%M%S')
        return {
            'name': f'测试任务_{timestamp}',
            'template': 'PythonTask',
            'code': 'def run(params, logger):\n    return "ok"',
            'name_edit': f'测试任务_{timestamp}_edit',
        }

    async def create_task(self, name: str, code: str) -> None:
        """新增任务：选模板 -> 低代码渲染参数 -> 填代码 -> 单次触发"""
        await self.page.get_by_role('button', name='新增').click()
        dialog = self.page.get_by_role('dialog')
        await dialog.wait_for()

        await dialog.get_by_role('textbox', name='任务名称').fill(name)

        # 选择任务模板(PythonTask -> 动态配置, 触发低代码渲染)
        await dialog.locator("label:has-text('任务模板') + div .el-select").click()
        await self.page.get_by_role('option', name='Python脚本任务 (PythonTask)').click()

        # 低代码渲染出的「Python代码」字段(按占位符定位)
        await dialog.get_by_placeholder('需定义 run(params, logger) 函数').fill(code)

        await dialog.get_by_role('button', name='确 定').click()
        await self.wait_for_selector("div:has-text('新增成功')", timeout=10000)

    async def search_task(self, name: str) -> None:
        form = self.page.locator('form').first
        await form.get_by_role('textbox', name='任务名称').fill(name)
        await self.page.get_by_role('button', name='搜索').click()
        await self.page.wait_for_timeout(1000)

    async def run_task_once(self, name: str) -> None:
        await self.search_task(name)
        row = self.page.locator('tbody tr').first
        await row.get_by_role('button', name='执行').click()
        await self.page.get_by_role('button', name='确定').click()
        await self.wait_for_selector("div:has-text('已触发执行')", timeout=10000)

    async def open_records_drawer(self, name: str) -> None:
        """点击「记录」打开执行记录抽屉"""
        await self.search_task(name)
        row = self.page.locator('tbody tr').first
        await row.get_by_role('button', name='记录').click()
        # 抽屉标题包含「执行记录」
        await self.wait_for_selector('text=执行记录', timeout=10000)
        # 关闭抽屉
        await self.page.keyboard.press('Escape')
        await self.page.wait_for_timeout(500)

    async def delete_task(self, name: str) -> None:
        await self.search_task(name)
        row = self.page.locator('tbody tr').first
        await row.get_by_role('button', name='删除').click()
        await self.page.get_by_role('button', name='确定').click()
        await self.wait_for_selector("div:has-text('删除成功')", timeout=10000)

    async def test_task_crud_operations(self) -> None:
        data = self.generate_task_data()

        await self.goto_page(Config.frontend_url + '/task/info')
        await self.wait_for_selector('text=任务名称')

        await self.create_task(data['name'], data['code'])
        await self.run_task_once(data['name'])
        await self.open_records_drawer(data['name'])
        await self.delete_task(data['name'])


@pytest.mark.asyncio
async def test_task_management_page() -> None:
    """测试任务管理页面(低代码表单 + 执行记录抽屉)"""
    async with async_playwright() as p:
        test_instance = TaskManagementTest()
        await test_instance.setup(p)
        try:
            await test_instance.test_task_crud_operations()
        finally:
            await test_instance.teardown()
