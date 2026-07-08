from datetime import datetime

import pytest
from playwright.async_api import async_playwright

from common.base_page_test import BasePageTest
from common.config import Config


class TaskTemplateManagementTest(BasePageTest):
    """任务模板管理测试(含低代码参数设计器)"""

    def generate_template_data(self) -> dict:
        timestamp = datetime.now().strftime('%H%M%S')
        return {
            'name': f'测试模板_{timestamp}',
            'code': f'TestTpl{timestamp}',
            'field': 'demo_field',
            'field_label': '演示字段',
            'name_edit': f'测试模板_{timestamp}_edit',
        }

    async def create_template(self, name: str, code: str, field: str, field_label: str) -> None:
        """新增动态配置模板，并用低代码设计器添加一个字段"""
        await self.page.get_by_role('button', name='新增').click()
        dialog = self.page.get_by_role('dialog')
        await dialog.wait_for()

        await dialog.get_by_role('textbox', name='模板名称').fill(name)
        await dialog.get_by_role('textbox', name='模板编码').fill(code)

        # 表单类型默认「动态配置」(type=2) -> 显示参数表单设计器(低代码)
        await dialog.get_by_role('button', name='添加字段').click()
        # 设计器新行：按占位符填写字段标识与标签
        await dialog.get_by_placeholder('如 code').first.fill(field)
        await dialog.get_by_placeholder('如 Python代码').first.fill(field_label)

        await dialog.get_by_role('button', name='确 定').click()
        await self.wait_for_selector("div:has-text('新增成功')", timeout=10000)

    async def search_template(self, name: str) -> None:
        form = self.page.locator('form').first
        await form.get_by_role('textbox', name='模板名称').fill(name)
        await self.page.get_by_role('button', name='搜索').click()
        await self.page.wait_for_timeout(1000)

    async def edit_template(self, name: str, new_name: str) -> None:
        await self.search_template(name)
        row = self.page.locator('tbody tr').first
        await row.get_by_role('button', name='修改').click()
        dialog = self.page.get_by_role('dialog')
        await dialog.wait_for()
        await dialog.get_by_role('textbox', name='模板名称').fill(new_name)
        await dialog.get_by_role('button', name='确 定').click()
        await self.wait_for_selector("div:has-text('修改成功')", timeout=10000)

    async def delete_template(self, name: str) -> None:
        await self.search_template(name)
        row = self.page.locator('tbody tr').first
        await row.get_by_role('button', name='删除').click()
        await self.page.get_by_role('button', name='确定').click()
        await self.wait_for_selector("div:has-text('删除成功')", timeout=10000)

    async def test_template_crud_operations(self) -> None:
        data = self.generate_template_data()

        await self.goto_page(Config.frontend_url + '/task/template')
        await self.wait_for_selector('text=模板名称')

        # 内置模板存在(PythonTask/ShellTask)
        await self.wait_for_selector('text=PythonTask', timeout=10000)

        await self.create_template(data['name'], data['code'], data['field'], data['field_label'])
        await self.edit_template(data['name'], data['name_edit'])
        await self.delete_template(data['name_edit'])


@pytest.mark.asyncio
async def test_task_template_management_page() -> None:
    """测试任务模板管理页面(低代码设计器)"""
    async with async_playwright() as p:
        test_instance = TaskTemplateManagementTest()
        await test_instance.setup(p)
        try:
            await test_instance.test_template_crud_operations()
        finally:
            await test_instance.teardown()
