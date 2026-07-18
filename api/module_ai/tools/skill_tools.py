"""Agent Skills 运行支撑(类 Claude Skills 的渐进式披露)。

- build_skill_catalog(skills):把「已启用/绑定技能」的 名称+描述+code 拼成常驻清单,注入 agent 指令(L1,便宜)。
- SkillTools.load_skill(code):任务匹配某技能时按 code 拉取该技能完整正文 SKILL.md(L2,按需进上下文)。

技能内容在装配 agent 前已从 DB 预加载进内存(避免工具调用时再打 DB / async-in-sync),
load_skill 只是从内存映射取出返回。
"""

from __future__ import annotations

from typing import Any

from agno.tools import Toolkit


def build_skill_catalog(skills: list[dict] | None) -> str:
    """生成「可用技能」常驻清单(注入 system 指令)。空则返回空串。

    只列 catalog!=False 的技能——仅因被别的技能软引用而带入的(catalog=False)不进常驻清单,
    但仍可被 load_skill 加载(通过引用它的技能的 load_skill 输出指引)。
    """
    if not skills:
        return ''
    listed = [s for s in skills if s.get('catalog', True)]
    if not listed:
        return ''
    lines = [
        '## 可用技能(Skills)',
        '下列技能是为特定任务预置的操作指南。当用户需求匹配某技能的用途时,先调用 load_skill(该技能的 code) 拿到完整步骤,再严格按其指引完成;不匹配则忽略,正常回答。',
    ]
    for s in listed:
        lines.append(f"- `{s.get('code')}`:{s.get('name')} —— {s.get('description') or ''}")
    return '\n'.join(lines)


class SkillTools(Toolkit):
    """技能加载工具集:load_skill 拉正文(SKILL.md),read_skill_file 按需拉附加文件。"""

    def __init__(self, skills: list[dict] | None = None, **kwargs: Any) -> None:
        # skills: [{code,name,description,content,files}](内容已预加载)
        #   content = SKILL.md 入口;files = [{name,content}] 附加文本文件
        self._skills: dict[str, dict] = {s['code']: s for s in (skills or []) if s.get('code')}
        super().__init__(name='skill', tools=[self.load_skill, self.read_skill_file], **kwargs)

    def load_skill(self, skill_code: str) -> str:
        """加载一个技能的完整操作指南(SKILL.md 正文)。

        当用户任务匹配「可用技能」清单里某技能的用途时调用:传入该技能 code,
        得到详细步骤/规范/示例,然后严格照做。技能若附带其它文件,正文末尾会列出,
        需要时再用 read_skill_file(skill_code, 文件名) 逐个拉取(文件级按需加载)。

        Args:
            skill_code: 技能代码(来自系统提示「可用技能」清单中的 code)
        """
        s = self._skills.get(skill_code)
        if not s:
            avail = ', '.join(self._skills.keys()) or '(无)'
            return f'未找到技能「{skill_code}」。当前可用技能 code:{avail}'
        content = (s.get('content') or '').strip()
        files = s.get('files') or []
        if not content and not files:
            return f'技能「{skill_code}」({s.get("name")})暂无正文内容。'
        out = f'# 技能:{s.get("name")}({skill_code})\n\n{content}'
        if files:
            names = ', '.join(f['name'] for f in files if f.get('name'))
            out += f'\n\n---\n本技能附带文件:{names}\n需要某个文件时,调用 read_skill_file("{skill_code}", "文件名") 拉取其内容。'
        refs = [c for c in (s.get('refs') or []) if c in self._skills]
        if refs:
            out += f'\n\n本技能引用了其它技能:{", ".join(refs)}\n需要时用 load_skill("引用的code") 加载它们(渐进式,按需)。'
        return out

    def read_skill_file(self, skill_code: str, filename: str) -> str:
        """读取某技能附带的一个文件正文(参考文档 / 脚本模板等)。

        仅当 load_skill 返回的「附带文件」清单里列出该文件时调用。脚本类文件返回的是其
        文本内容——需要执行时,把内容复制到 run_python_code 里跑(沙箱无磁盘,不能直接执行文件)。

        Args:
            skill_code: 技能代码
            filename: 文件名(来自 load_skill 输出的「附带文件」清单)
        """
        s = self._skills.get(skill_code)
        if not s:
            return f'未找到技能「{skill_code}」。'
        files = s.get('files') or []
        for f in files:
            if f.get('name') == filename:
                body = (f.get('content') or '').strip()
                return body or f'文件「{filename}」为空。'
        avail = ', '.join(x['name'] for x in files if x.get('name')) or '(无附加文件)'
        return f'技能「{skill_code}」下未找到文件「{filename}」。可用文件:{avail}'
