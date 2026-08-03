import asyncio
import time
from typing import Any

from sqlalchemy import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_ai.dao.ai_model_dao import AiModelDao
from module_ai.entity.vo.ai_model_vo import AiModelModel, AiModelPageQueryModel, DeleteAiModelModel
from utils.ai_util import AiUtil
from utils.common_util import CamelCaseUtil
from utils.crypto_util import CryptoUtil


class AiModelService:
    """
    AI模型管理服务层
    """

    @classmethod
    async def get_ai_model_list_services(
        cls,
        query_db: AsyncSession,
        query_object: AiModelPageQueryModel,
        data_scope_sql: ColumnElement,
        is_page: bool = False,
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取AI模型列表信息service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :param is_page: 是否开启分页
        :return: AI模型列表信息对象
        """
        ai_model_list_result = await AiModelDao.get_ai_model_list(query_db, query_object, data_scope_sql, is_page)
        rows = ai_model_list_result.rows if isinstance(ai_model_list_result, PageModel) else ai_model_list_result

        for row in rows:
            if 'apiKey' in row:
                row['apiKey'] = '********' * 3

        return ai_model_list_result

    @classmethod
    async def get_chat_models_with_default(
        cls,
        query_db: AsyncSession,
        data_scope_sql: ColumnElement,
    ) -> list[dict[str, Any]]:
        """获取「AI 选模型」可用列表:全部启用模型;若配置了环境变量兜底模型则在首位插入默认项。"""
        from config.env import AiConfig

        rows = await cls.get_ai_model_list_services(
            query_db, AiModelPageQueryModel(status='0'), data_scope_sql, is_page=False
        )

        result: list[dict[str, Any]] = []
        if AiConfig.enabled:
            result.append(
                {
                    'modelId': 0,
                    'provider': AiConfig.provider,
                    'modelCode': AiConfig.llm_model,
                    'modelName': '默认模型',
                    'maxTokens': AiConfig.llm_max_tokens,
                    'temperature': None,
                    'supportReasoning': 'N',
                    'supportImages': 'N',
                    'status': '0',
                    'isDefault': True,
                    'apiKey': '********' * 3,
                }
            )
        result.extend(rows)
        return result

    @classmethod
    async def check_ai_model_data_scope_services(
        cls,
        query_db: AsyncSession,
        model_id: int,
        data_scope_sql: ColumnElement,
    ) -> CrudResponseModel:
        """
        校验用户是否有AI模型数据权限service

        :param query_db: orm对象
        :param model_id: 模型主键
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 校验结果
        """
        ai_models = await AiModelDao.get_ai_model_list(
            query_db, AiModelModel(modelId=model_id), data_scope_sql, is_page=False
        )
        if ai_models:
            return CrudResponseModel(is_success=True, message='校验通过')
        raise ServiceException(message='没有权限访问AI模型数据')

    @classmethod
    async def add_ai_model_services(cls, query_db: AsyncSession, page_object: AiModelModel) -> CrudResponseModel:
        """
        新增AI模型信息service

        :param request: Request对象
        :param query_db: orm对象
        :param page_object: 新增AI模型对象
        :return: 新增AI模型校验结果
        """
        try:
            if page_object.api_key:
                page_object.api_key = CryptoUtil.encrypt(page_object.api_key)
            await AiModelDao.add_ai_model_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_ai_model_services(cls, query_db: AsyncSession, page_object: AiModelModel) -> CrudResponseModel:
        """
        编辑AI模型信息service

        :param query_db: orm对象
        :param page_object: 编辑AI模型对象
        :return: 编辑AI模型校验结果
        """
        edit_ai_model = page_object.model_dump(exclude_unset=True)
        if page_object.api_key:
            if page_object.api_key == '********' * 3:
                if 'api_key' in edit_ai_model:
                    del edit_ai_model['api_key']
            else:
                edit_ai_model['api_key'] = CryptoUtil.encrypt(page_object.api_key)

        ai_model_info = await cls.ai_model_detail_services(query_db, page_object.model_id)
        if ai_model_info.model_id:
            try:
                await AiModelDao.edit_ai_model_dao(query_db, edit_ai_model)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='修改成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='AI模型不存在')

    @classmethod
    async def delete_ai_model_services(
        cls, query_db: AsyncSession, page_object: DeleteAiModelModel
    ) -> CrudResponseModel:
        """
        删除AI模型信息service

        :param query_db: orm对象
        :param page_object: 删除AI模型对象
        :return: 删除AI模型校验结果
        """
        if page_object.model_ids:
            model_id_list = page_object.model_ids.split(',')
            try:
                for model_id in model_id_list:
                    await AiModelDao.delete_ai_model_dao(query_db, AiModelModel(modelId=model_id))
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入AI模型id为空')

    @classmethod
    async def test_ai_model_services(cls, query_db: AsyncSession, page_object: AiModelModel) -> dict[str, Any]:
        """测试连接:用表单/库内配置真跑一次极小的流式补全,回连通性、时延与真实用量。

        api_key 解析:表单填了明文用表单的;传的是掩码(编辑已存模型未改密钥)或空且有 model_id,
        则回读库内并解密。其余缺省字段(provider/model_code/base_url/max_tokens)同样用库内兜底。
        与「数据源测试连接」一致——失败不抛异常,而是回 {success: False, message},由前端就地展示。
        """
        api_key = page_object.api_key
        masked = api_key == '********' * 3
        if (not api_key or masked) and page_object.model_id:
            ai_model = await AiModelDao.get_ai_model_detail_by_id(query_db, page_object.model_id)
            if ai_model:
                stored = AiModelModel(**CamelCaseUtil.transform_result(ai_model))
                if stored.api_key:
                    api_key = CryptoUtil.decrypt(stored.api_key)
                page_object.provider = page_object.provider or stored.provider
                page_object.model_code = page_object.model_code or stored.model_code
                page_object.base_url = page_object.base_url or stored.base_url
                page_object.max_tokens = page_object.max_tokens or stored.max_tokens
        if not page_object.provider or not page_object.model_code:
            raise ServiceException(message='缺少提供商或模型编码')
        if not api_key or api_key == '********' * 3:
            raise ServiceException(message='缺少 API Key:新模型请在表单填写,已存模型请确认已保存过密钥')

        return await cls._probe_model(
            provider=page_object.provider,
            model_code=page_object.model_code,
            api_key=api_key,
            base_url=page_object.base_url or None,
            max_tokens=page_object.max_tokens,
        )

    @classmethod
    async def _probe_model(
        cls,
        *,
        provider: str,
        model_code: str,
        api_key: str,
        base_url: str | None,
        max_tokens: int | None,
    ) -> dict[str, Any]:
        """构建模型并流式跑一句话,采集用量(与生产同一 factory 路径,故用量已按 metrics 修正口径)。"""
        from agno.agent import Agent

        started = time.perf_counter()
        completion_metrics = AiUtil._wants_completion_metrics(provider, base_url)
        try:
            model = AiUtil.get_model_from_factory(
                provider=provider,
                model_code=model_code,
                api_key=api_key,
                base_url=base_url,
                temperature=0,
                max_tokens=min(int(max_tokens or 64), 64),  # 探针只需极少输出
            )
            agent = Agent(model=model, telemetry=False)

            reply_parts: list[str] = []
            metrics: dict[str, Any] = {}

            async def _run() -> None:
                async for ev in agent.arun('用简短一句话回复「连接正常」即可,不要调用任何工具。', stream=True):
                    content = getattr(ev, 'content', None)
                    if isinstance(content, str):
                        reply_parts.append(content)
                    m = getattr(ev, 'metrics', None)
                    if m is not None and hasattr(m, 'to_dict'):
                        md = m.to_dict()
                        if md:
                            metrics.clear()
                            metrics.update(md)

            await asyncio.wait_for(_run(), timeout=45)
        except (TimeoutError, asyncio.TimeoutError):
            return {'success': False, 'message': '测试超时(45s):检查网络 / base_url / 模型是否可用'}
        except Exception as e:
            return {'success': False, 'message': f'调用失败:{str(e)[:300]}', 'completionMetrics': completion_metrics}

        it = int(metrics.get('input_tokens') or 0)
        ot = int(metrics.get('output_tokens') or 0)
        tt = int(metrics.get('total_tokens') or (it + ot))
        return {
            'success': True,
            'message': '连接正常',
            'latencyMs': round((time.perf_counter() - started) * 1000),
            'reply': ''.join(reply_parts).strip()[:200],
            'inputTokens': it,
            'outputTokens': ot,
            'totalTokens': tt,
            # 该网关是否被判定为「需仅收尾采一次 usage」(治 token 放大):便于用户核对用量口径
            'completionMetrics': completion_metrics,
        }

    @classmethod
    async def ai_model_detail_services(cls, query_db: AsyncSession, model_id: int) -> AiModelModel:
        """
        获取AI模型详细信息service

        :param query_db: orm对象
        :param model_id: AI模型id
        :return: AI模型id对应的信息
        """
        ai_model = await AiModelDao.get_ai_model_detail_by_id(query_db, model_id=model_id)
        result = AiModelModel(**CamelCaseUtil.transform_result(ai_model)) if ai_model else AiModelModel()

        if result.api_key:
            result.api_key = '********' * 3

        return result
