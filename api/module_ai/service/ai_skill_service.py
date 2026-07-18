from typing import Any

from sqlalchemy import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_ai.dao.ai_skill_dao import AiSkillDao
from module_ai.entity.vo.ai_skill_vo import AiSkillModel, AiSkillPageQueryModel, DeleteAiSkillModel
from utils.common_util import CamelCaseUtil


class AiSkillService:
    """AI技能管理服务层(Agent Skills)"""

    @classmethod
    async def get_ai_skill_list_services(
        cls, query_db: AsyncSession, query_object: AiSkillPageQueryModel, data_scope_sql: ColumnElement, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        return await AiSkillDao.get_ai_skill_list(query_db, query_object, data_scope_sql, is_page)

    @classmethod
    async def add_ai_skill_services(cls, query_db: AsyncSession, page_object: AiSkillModel) -> CrudResponseModel:
        if await AiSkillDao.get_ai_skill_by_code(query_db, page_object.code):
            raise ServiceException(message=f'技能代码已存在: {page_object.code}')
        data = page_object.model_dump(exclude_unset=True)
        data.pop('skill_id', None)
        data['built_in'] = '0'
        try:
            await AiSkillDao.add_ai_skill_dao(query_db, data)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_ai_skill_services(cls, query_db: AsyncSession, page_object: AiSkillModel) -> CrudResponseModel:
        existing = await AiSkillDao.get_ai_skill_detail_by_id(query_db, page_object.skill_id)
        if not existing:
            raise ServiceException(message='技能不存在')
        data = page_object.model_dump(exclude_unset=True)
        if existing.built_in == '1':
            data.pop('code', None)  # 内置技能禁止改 code
        elif data.get('code') and data['code'] != existing.code:
            if await AiSkillDao.get_ai_skill_by_code(query_db, data['code']):
                raise ServiceException(message=f'技能代码已存在: {data["code"]}')
        data['skill_id'] = page_object.skill_id
        try:
            await AiSkillDao.edit_ai_skill_dao(query_db, data)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def delete_ai_skill_services(cls, query_db: AsyncSession, page_object: DeleteAiSkillModel) -> CrudResponseModel:
        if not page_object.skill_ids:
            raise ServiceException(message='传入技能id为空')
        try:
            for sid in page_object.skill_ids.split(','):
                existing = await AiSkillDao.get_ai_skill_detail_by_id(query_db, int(sid))
                if existing and existing.built_in == '1':
                    raise ServiceException(message=f'内置技能不可删除: {existing.name}')
                await AiSkillDao.delete_ai_skill_dao(query_db, int(sid))
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except ServiceException:
            await query_db.rollback()
            raise
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def ai_skill_detail_services(cls, query_db: AsyncSession, skill_id: int) -> AiSkillModel:
        obj = await AiSkillDao.get_ai_skill_detail_by_id(query_db, skill_id)
        if not obj:
            return AiSkillModel()
        return AiSkillModel(**CamelCaseUtil.transform_result(obj))

    # 软引用展开的最大深度(A→B→C…),防循环/上下文膨胀
    _REF_MAX_DEPTH = 3

    @classmethod
    async def resolve_agent_skills(
        cls, query_db: AsyncSession, skill_ids: list[int] | None, *, scope_codes: list[str] | None = None
    ) -> list[dict]:
        """装配 agent 用的技能清单 [{code,name,description,content,files,refs,skill_type,ds_codes,catalog}]。

        skill_ids 为空 → 全部启用(普通对话);否则按应用绑定的 id 取(启用的)。
        scope_codes:本次对话可访问的数据源 code(应用绑定的数据源;普通对话传 None=全部)。
        - files:附加文本文件 [{name,content}](供 read_skill_file 按需拉取)。
        - refs:软引用的技能 code 列表。skill_type:process流程型 / knowledge知识型。ds_codes:知识型绑定的源。
        - catalog:是否进 L1 常驻清单:
            · 流程型 → 总是 True。
            · 知识型 → 仅当其绑定源命中本次 scope(应用场景)才 True;普通对话(scope=None)→ False,
              改由 search_datasource_knowledge 在「认源」时浮现(见 data_agent_tools)。
            · 仅因被引用带入的 → False(可 load,不占常驻)。
        软引用做有界 BFS 展开(深度≤_REF_MAX_DEPTH、visited 去重)。
        """
        scope = set(scope_codes) if scope_codes else set()
        rows = await AiSkillDao.list_enabled(query_db, skill_ids or None)
        by_code: dict[str, dict] = {}
        for r in rows:
            by_code[r.code] = cls._to_skill_dict(r, catalog=cls._catalog_for(r, scope))

        # BFS 展开引用:逐层收集尚未在 by_code 里的引用 code,按 code 补取(catalog=False)
        frontier = {c for s in by_code.values() for c in s['refs']} - set(by_code.keys())
        depth = 0
        while frontier and depth < cls._REF_MAX_DEPTH:
            ref_rows = await AiSkillDao.get_by_codes(query_db, list(frontier))
            next_frontier: set[str] = set()
            for r in ref_rows:
                if r.code not in by_code:
                    d = cls._to_skill_dict(r, catalog=False)
                    by_code[r.code] = d
                    next_frontier |= set(d['refs'])
            frontier = next_frontier - set(by_code.keys())
            depth += 1
        return list(by_code.values())

    @classmethod
    def _catalog_for(cls, r, scope: set) -> bool:
        """L1 常驻清单准入:流程型总进;知识型仅当绑定源命中 scope(空 scope=普通对话→不进,靠浮现)。"""
        if (getattr(r, 'skill_type', None) or 'process') != 'knowledge':
            return True
        return bool(scope) and bool(set(cls._parse_refs(getattr(r, 'datasource_codes', None))) & scope)

    @classmethod
    def _to_skill_dict(cls, r, catalog: bool) -> dict:
        return {
            'code': r.code,
            'name': r.name,
            'description': r.description or '',
            'content': r.content or '',
            'files': cls._parse_files(r.resources),
            'refs': cls._parse_refs(getattr(r, 'ref_skills', None)),
            'skill_type': (getattr(r, 'skill_type', None) or 'process'),
            'ds_codes': cls._parse_refs(getattr(r, 'datasource_codes', None)),
            'catalog': catalog,
        }

    @staticmethod
    def _parse_refs(ref_skills: str | None) -> list[str]:
        """把 ref_skills(逗号分隔 code)解析成去重的 code 列表。"""
        if not ref_skills:
            return []
        seen, out = set(), []
        for c in str(ref_skills).split(','):
            c = c.strip()
            if c and c not in seen:
                seen.add(c)
                out.append(c)
        return out

    @staticmethod
    def _parse_files(resources: str | None) -> list[dict]:
        """把 resources JSON 解析成 [{name,content}];非法/空则返回 []。"""
        import json

        if not resources:
            return []
        try:
            data = json.loads(resources)
        except (ValueError, TypeError):
            return []
        if not isinstance(data, list):
            return []
        out = []
        for f in data:
            if isinstance(f, dict) and f.get('name'):
                out.append({'name': str(f['name']), 'content': str(f.get('content') or '')})
        return out
