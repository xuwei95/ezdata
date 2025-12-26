"""
LLM工具管理API
"""
import json
import traceback
from flask import Blueprint, request, jsonify
from utils.common_utils import gen_json_response, gen_uuid
from utils.auth import validate_user, set_insert_user, set_update_user
from web_apps import db
from web_apps.llm.db_models import LLMTool
from web_apps.llm.tools import tools_map
from utils.logger.logger import get_logger

logger = get_logger(p_name='system_log', f_name='llm_tool', log_level='INFO')
tool_bp = Blueprint('llm_tool', __name__)


@tool_bp.route('/list', methods=['GET'])
@validate_user
def tool_list():
    """获取工具列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 10, type=int)
        tool_type = request.args.get('type', '')
        keyword = request.args.get('keyword', '')

        query = db.session.query(LLMTool)

        if tool_type:
            query = query.filter(LLMTool.type == tool_type)

        if keyword:
            query = query.filter(
                db.or_(
                    LLMTool.name.like(f'%{keyword}%'),
                    LLMTool.code.like(f'%{keyword}%'),
                    LLMTool.description.like(f'%{keyword}%')
                )
            )

        total = query.count()
        tools = query.offset((page - 1) * page_size).limit(page_size).all()

        data = [tool.to_dict() for tool in tools]
        res_data = {
            'records': data,
            'total': total,
        }
        return gen_json_response(data=res_data)
    except Exception as e:
        logger.error(f"获取工具列表失败: {str(e)}")
        return gen_json_response(msg=str(e))

@tool_bp.route('/<tool_id>', methods=['GET'])
@validate_user
def get_tool_detail(tool_id):
    """获取工具详情"""
    try:
        tool = db.session.query(LLMTool).filter(LLMTool.id == tool_id).first()
        if not tool:
            return gen_json_response(code=400, msg='工具不存在')

        return gen_json_response(data=tool.to_dict())
    except Exception as e:
        logger.error(f"获取工具详情失败: {str(e)}")
        return gen_json_response(code=500, msg=str(e))


@tool_bp.route('/add', methods=['POST'])
@validate_user
def add_tool():
    """添加工具"""
    try:
        req_data = request.get_json()

        # 检查工具类型
        tool_type = req_data.get('type')
        if tool_type != 'mcp':
            return gen_json_response(code=400, msg='目前只支持MCP工具类型')

        # 检查代码是否已存在
        existing_tool = db.session.query(LLMTool).filter(LLMTool.code == req_data.get('code')).first()
        if existing_tool:
            return gen_json_response(code=400, msg='工具代码已存在')

        tool = LLMTool(
            id=gen_uuid(),
            name=req_data.get('name'),
            code=req_data.get('code'),
            type=req_data.get('type'),
            description=req_data.get('description', ''),
            args=json.dumps(req_data.get('args', {}), ensure_ascii=False),
            status=req_data.get('status', 1)
        )

        set_insert_user(tool)

        db.session.add(tool)
        db.session.commit()

        logger.info(f"添加工具成功: {tool.name}")
        return gen_json_response(data=tool.to_dict(), msg='添加成功', extends={'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"添加工具失败: {str(e)}")
        return gen_json_response(code=500, msg=str(e))


@tool_bp.route('/edit', methods=['POST'])
@validate_user
def edit_tool():
    """编辑工具"""
    try:
        req_data = request.get_json()
        tool_id = req_data.get('id')

        if not tool_id:
            return gen_json_response(code=400, msg='工具ID不能为空')

        tool = db.session.query(LLMTool).filter(LLMTool.id == tool_id).first()
        if not tool:
            return gen_json_response(code=500, msg='工具不存在')

        # 检查工具类型
        if 'type' in req_data and req_data.get('type') != 'mcp':
            return gen_json_response(code=400, msg='目前只支持MCP工具类型')

        # 检查代码是否重复
        if req_data.get('code') and req_data.get('code') != tool.code:
            existing_tool = db.session.query(LLMTool).filter(
                LLMTool.code == req_data.get('code'),
                LLMTool.id != tool_id
            ).first()
            if existing_tool:
                return gen_json_response(code=400, msg='工具代码已存在')

        tool.name = req_data.get('name', tool.name)
        tool.code = req_data.get('code', tool.code)
        if 'type' in req_data:
            tool.type = req_data.get('type')
        tool.description = req_data.get('description', tool.description)

        if 'args' in req_data:
            tool.args = json.dumps(req_data.get('args'), ensure_ascii=False)

        tool.status = req_data.get('status', tool.status)

        set_update_user(tool)

        db.session.commit()

        logger.info(f"编辑工具成功: {tool.name}")
        return gen_json_response(data=tool.to_dict(), msg='编辑成功', extends={'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"编辑工具失败: {str(e)}")
        return gen_json_response(code=500, msg=str(e))


@tool_bp.route('/delete', methods=['DELETE'])
@validate_user
def delete_tool():
    """删除工具"""
    try:
        req_data = request.get_json()
        tool_id = req_data.get('id')

        if not tool_id:
            return gen_json_response(code=400, msg='工具ID不能为空')

        tool = db.session.query(LLMTool).filter(LLMTool.id == tool_id).first()
        if not tool:
            return gen_json_response(code=500, msg='工具不存在')

        db.session.delete(tool)
        db.session.commit()

        logger.info(f"删除工具成功: {tool.name}")
        return gen_json_response(msg='删除成功', extends={'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除工具失败: {str(e)}")
        return gen_json_response(code=500, msg=str(e))


@tool_bp.route('/test', methods=['POST'])
@validate_user
def test_tool():
    """测试MCP工具连接（根据配置直接测试）"""
    try:
        req_data = request.get_json()

        # 获取配置参数
        tool_type = req_data.get('type')
        tool_code = req_data.get('code')
        tool_config = req_data.get('args', {})

        if not tool_code:
            return gen_json_response(code=400, msg='工具代码不能为空')

        if tool_type != 'mcp':
            return gen_json_response(code=400, msg='只支持测试MCP工具')

        if not tool_config:
            return gen_json_response(code=400, msg='工具配置不能为空')

        # 构建 MCP 工具配置
        server_name = tool_code
        server_type = tool_config.get('server_type', 'stdio')
        params = {}

        if server_type == 'stdio':
            command = tool_config.get('command', '').strip()
            if not command:
                return gen_json_response(code=400, msg='STDIO 模式下执行命令不能为空')

            params = {
                "command": command,
                "args": tool_config.get('args', []),
                "transport": "stdio"
            }
            # 添加环境变量（如果有）
            if tool_config.get('env'):
                params['env'] = tool_config.get('env')

        elif server_type in ['sse', 'streamable_http']:
            url = tool_config.get('url', '').strip()
            if not url:
                return gen_json_response(code=400, msg='SSE 模式下服务器URL不能为空')

            params = {
                "url": url,
                "transport": "streamable_http"
            }
            # 添加请求头（如果有）
            if tool_config.get('headers'):
                params['headers'] = tool_config.get('headers')
        else:
            return gen_json_response(code=400, msg=f'不支持的服务器类型: {server_type}')

        mcp_tool_config = {server_name: params}

        # 测试加载工具
        import asyncio
        from langchain_mcp_adapters.client import MultiServerMCPClient

        async def test_load():
            client = MultiServerMCPClient(mcp_tool_config)
            tools = await client.get_tools()
            return tools

        logger.info(f"开始测试MCP工具: {server_name}, 配置: {params}")
        tools = asyncio.run(test_load())

        if not tools:
            return gen_json_response(code=500, msg='工具加载失败：未获取到任何工具')

        # 返回成功信息
        tool_info = [{'name': t.name, 'description': t.description} for t in tools]
        result = {
            'server': server_name,
            'tools_count': len(tools),
            'tools': tool_info
        }

        logger.info(f"测试MCP工具成功: {server_name}, 获取到 {len(tools)} 个工具")
        return gen_json_response(data=result, msg=f'连接成功！获取到 {len(tools)} 个工具')

    except Exception as e:
        error_msg = f"测试工具失败: {str(e)}"
        logger.error(error_msg)
        import traceback
        logger.error(traceback.format_exc())
        return gen_json_response(code=500, msg=error_msg)


@tool_bp.route('/types', methods=['GET'])
@validate_user
def get_tool_types():
    """获取工具类型列表"""
    try:
        tool_types = [
            {'value': 'mcp', 'label': 'MCP工具'},
        ]
        return gen_json_response(data=tool_types)
    except Exception as e:
        logger.error(f"获取工具类型失败: {str(e)}")
        return gen_json_response(code=500, msg=str(e))


@tool_bp.route('/queryAllList', methods=['GET'])
@validate_user
def query_all_list():
    """查询所有工具列表（内置工具 + 数据库工具），用于下拉选择"""
    try:
        tool_list = []

        # 1. 获取所有内置工具
        for key, info in tools_map.items():
            tool_list.append({
                'name': info['name'],
                'value': key
            })

        # 2. 获取数据库中的工具（只查询启用的）
        db_tools = db.session.query(LLMTool).filter(
            LLMTool.status == 1
        ).order_by(LLMTool.create_time.desc()).all()

        for tool in db_tools:
            tool_list.append({
                'name': tool.name,
                'value': tool.id
            })

        logger.info(f"查询所有工具列表成功，共 {len(tool_list)} 个工具")
        return gen_json_response(data=tool_list)

    except Exception as e:
        logger.error(f"查询工具列表失败: {str(e)}")
        logger.error(traceback.format_exc())
        return gen_json_response(code=500, msg=str(e))
