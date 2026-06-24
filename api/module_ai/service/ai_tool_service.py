import json
from typing import Any

from sqlalchemy import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_ai.dao.ai_tool_dao import AiToolDao
from module_ai.entity.vo.ai_tool_vo import AiToolModel, AiToolPageQueryModel, DeleteAiToolModel
from utils.common_util import CamelCaseUtil


def _dumps(args: Any) -> str:
    if isinstance(args, str):
        return args
    return json.dumps(args or {}, ensure_ascii=False)


def _loads(args: Any) -> Any:
    if isinstance(args, str):
        try:
            return json.loads(args)
        except (ValueError, TypeError):
            return {}
    return args if args is not None else {}


class AiToolService:
    """
    AI工具管理服务层
    """

    @classmethod
    async def get_ai_tool_list_services(
        cls, query_db: AsyncSession, query_object: AiToolPageQueryModel,
        data_scope_sql: ColumnElement, is_page: bool = False,
    ) -> PageModel | list[dict[str, Any]]:
        """获取工具列表(args JSON 串还原为对象)"""
        result = await AiToolDao.get_ai_tool_list(query_db, query_object, data_scope_sql, is_page)
        rows = result.rows if isinstance(result, PageModel) else result
        for row in rows:
            if 'args' in row:
                row['args'] = _loads(row['args'])
        return result

    @classmethod
    async def add_ai_tool_services(cls, query_db: AsyncSession, page_object: AiToolModel) -> CrudResponseModel:
        """新增工具"""
        if await AiToolDao.get_ai_tool_by_code(query_db, page_object.code):
            raise ServiceException(message=f'工具代码已存在: {page_object.code}')
        data = page_object.model_dump(exclude_unset=True)
        data.pop('tool_id', None)
        data['tool_type'] = data.get('tool_type') or 'mcp'
        data['args'] = _dumps(data.get('args'))
        data['built_in'] = '0'  # 经接口新增的一律非内置
        try:
            await AiToolDao.add_ai_tool_dao(query_db, data)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_ai_tool_services(cls, query_db: AsyncSession, page_object: AiToolModel) -> CrudResponseModel:
        """编辑工具(内置工具仅允许改名称/描述/状态/备注,禁止改 code/类型)"""
        existing = await AiToolDao.get_ai_tool_detail_by_id(query_db, page_object.tool_id)
        if not existing:
            raise ServiceException(message='工具不存在')
        data = page_object.model_dump(exclude_unset=True)
        if 'args' in data:
            data['args'] = _dumps(data.get('args'))
        if existing.built_in == '1':
            data.pop('code', None)
            data.pop('tool_type', None)
        elif data.get('code') and data['code'] != existing.code:
            if await AiToolDao.get_ai_tool_by_code(query_db, data['code']):
                raise ServiceException(message=f'工具代码已存在: {data["code"]}')
        data['tool_id'] = page_object.tool_id
        try:
            await AiToolDao.edit_ai_tool_dao(query_db, data)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def delete_ai_tool_services(cls, query_db: AsyncSession, page_object: DeleteAiToolModel) -> CrudResponseModel:
        """删除工具(内置工具不可删除)"""
        if not page_object.tool_ids:
            raise ServiceException(message='传入工具id为空')
        try:
            for tid in page_object.tool_ids.split(','):
                existing = await AiToolDao.get_ai_tool_detail_by_id(query_db, int(tid))
                if existing and existing.built_in == '1':
                    raise ServiceException(message=f'内置工具不可删除: {existing.name}')
                await AiToolDao.delete_ai_tool_dao(query_db, int(tid))
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except ServiceException:
            await query_db.rollback()
            raise
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def ai_tool_detail_services(cls, query_db: AsyncSession, tool_id: int) -> AiToolModel:
        """获取工具详情"""
        obj = await AiToolDao.get_ai_tool_detail_by_id(query_db, tool_id)
        if not obj:
            return AiToolModel()
        result = AiToolModel(**CamelCaseUtil.transform_result(obj))
        result.args = _loads(result.args)
        return result

    @staticmethod
    def build_mcp_kwargs(args: dict, timeout_seconds: int = 15) -> dict:
        """把工具 args(server_type/command/args/env 或 url/headers)转成 agno MCPTools 构造参数。"""
        server_type = (args.get('server_type') or 'stdio').lower()
        kwargs: dict[str, Any] = {'timeout_seconds': timeout_seconds}
        if server_type == 'stdio':
            command = (args.get('command') or '').strip()
            if not command:
                raise ServiceException(message='请填写执行命令')
            cmd_args = args.get('args') or []
            full = command + ((' ' + ' '.join(str(a) for a in cmd_args)) if cmd_args else '')
            kwargs.update(command=full, transport='stdio')
            env = args.get('env') or {}
            if env:
                kwargs['env'] = {str(k): str(v) for k, v in env.items()}
        else:
            url = (args.get('url') or '').strip()
            if not url:
                raise ServiceException(message='请填写服务器URL')
            transport = 'streamable-http' if server_type in ('http', 'streamable-http', 'streamable_http') else 'sse'
            kwargs.update(url=url, transport=transport)
            headers = args.get('headers') or {}
            if headers:
                _h = {str(k): str(v) for k, v in headers.items()}
                kwargs['header_provider'] = lambda: _h
        return kwargs

    @classmethod
    async def resolve_app_tools(cls, query_db: AsyncSession, tool_ids: list[int]) -> dict:
        """按 ai_tool id 拆分:{'builtin_codes': [toolkit名...], 'mcp_configs': [{name,code,args}...]}。

        内置工具 code = toolkit 名(data_explore/sandbox_code/task_propose);MCP 工具给出连接配置。
        供 AI 应用按所选工具装配 agent。
        """
        from sqlalchemy import select  # noqa: PLC0415

        from module_ai.entity.do.ai_tool_do import AiTool  # noqa: PLC0415

        if not tool_ids:
            return {'builtin_codes': [], 'mcp_configs': []}
        rows = (await query_db.execute(
            select(AiTool).where(AiTool.tool_id.in_(tool_ids), AiTool.status == '0')
        )).scalars().all()
        builtin_codes = [r.code for r in rows if r.tool_type == 'builtin']
        mcp_configs = [{'name': r.name, 'code': r.code, 'args': _loads(r.args)}
                       for r in rows if r.tool_type == 'mcp']
        return {'builtin_codes': builtin_codes, 'mcp_configs': mcp_configs}

    @classmethod
    async def get_enabled_mcp_tools_by_ids(cls, query_db: AsyncSession, tool_ids: list[int]) -> list[dict]:
        """按 id 取启用的 MCP 工具,返回 [{name, code, args(dict)}](供 agent 装配)。"""
        from sqlalchemy import select  # noqa: PLC0415

        from module_ai.entity.do.ai_tool_do import AiTool  # noqa: PLC0415

        if not tool_ids:
            return []
        rows = (await query_db.execute(
            select(AiTool).where(AiTool.tool_id.in_(tool_ids), AiTool.tool_type == 'mcp', AiTool.status == '0')
        )).scalars().all()
        return [{'name': r.name, 'code': r.code, 'args': _loads(r.args)} for r in rows]

    @classmethod
    async def test_mcp_tool_services(cls, args: dict) -> dict:
        """用 agno MCPTools 试连一下 MCP server,返回其暴露的工具名/数。"""
        try:
            from agno.tools.mcp import MCPTools  # noqa: PLC0415
        except Exception as e:  # noqa: BLE001
            raise ServiceException(message=f'MCP 依赖未安装(需重建镜像后可测): {e}')

        kwargs = cls.build_mcp_kwargs(args)
        try:
            async with MCPTools(**kwargs) as t:
                names = sorted((getattr(t, 'functions', None) or {}).keys())
            return {'success': True, 'count': len(names), 'tools': names}
        except Exception as e:  # noqa: BLE001
            raise ServiceException(message=f'连接失败: {e}')
