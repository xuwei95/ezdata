"""配置加载:读 LLM 等环境变量(纯标准库解析)。

优先级:真实环境变量 > .env 文件。文件路径可用 EZDATA_ENV_FILE 覆盖;否则按下面顺序取第一个存在的:
  1) 本目录 interface/web/.env.dev、.env   —— 就近(适合从 web 目录直接跑,复制 .env.example 即可)
  2) api/.env.dev、api/.env               —— 兜底(平台 dev 配置)
"""

import os
from pathlib import Path

# ezdata/interface/web/config.py:_HERE.parent=web/,四级父级=api/
_HERE = Path(__file__).resolve()
_WEB_DIR = _HERE.parent
_API_DIR = _HERE.parent.parent.parent.parent
_DEFAULT_CANDIDATES = [
    _WEB_DIR / '.env.dev',   # interface/web/.env.dev(就近,优先)
    _WEB_DIR / '.env',       # interface/web/.env
    _API_DIR / '.env.dev',   # api/.env.dev(兜底)
    _API_DIR / '.env',
]


def _parse_env_file(path: Path) -> dict:
    """解析 KEY=VALUE(容忍空格、引号、行内注释以 # 开头的整行)。

    读取失败(如 docker 单文件挂载偶发 I/O error、权限、编码)时降级为空,
    不让配置加载拖垮整个进程启动。
    """
    out: dict[str, str] = {}
    try:
        text = path.read_text(encoding='utf-8', errors='ignore')
    except OSError as e:
        print(f'[config] 读取 env 文件失败({e}),跳过:{path}')
        return out
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, val = line.partition('=')
        key = key.strip()
        val = val.strip().strip('\'"').strip()
        if key:
            out[key] = val
    return out


def load_env() -> dict:
    """加载 .env 文件内容(不覆盖已存在的真实环境变量),返回合并后的映射。"""
    data: dict[str, str] = {}
    env_file = os.environ.get('EZDATA_ENV_FILE')
    candidates = [Path(env_file)] if env_file else _DEFAULT_CANDIDATES
    for p in candidates:
        if p and p.exists():
            data.update(_parse_env_file(p))
            break
    # 真实环境变量优先
    merged = {**data, **{k: v for k, v in os.environ.items() if k in data}}
    return merged


_ENV = load_env()


def get(key: str, default=None):
    return os.environ.get(key) or _ENV.get(key, default)


def llm_config() -> dict:
    """从 env 拼出 LLM 配置(供 ezdata.interface.web.llm 的 agno 客户端使用)。

    base_url:显式 LLM_URL 优先;未填时——openai 兼容族补 OpenAI 官方端点,
    anthropic 族留空(用官方端点,不误塞 openai 地址)。
    """
    llm_type = get('LLM_TYPE', 'openai') or 'openai'
    base_url = (get('LLM_URL', '') or '').rstrip('/')
    if not base_url and llm_type.strip().lower() not in ('anthropic', 'claude'):
        base_url = 'https://api.openai.com/v1'
    return {
        'type': llm_type,
        'api_key': get('LLM_API_KEY', ''),
        'base_url': base_url,
        'model': get('LLM_MODEL', 'gpt-4o-mini'),
        'max_tokens': int(get('LLM_MAX_TOKENS', '4096') or 4096),
    }


# 连接目录 SQLite 路径:默认锚定到 api 目录,和启动 cwd 无关——
# 这样无论从 api/ 还是从 interface/web/ 跑,用的都是同一份连接目录。可用 EZDATA_LOCAL_DB 覆盖。
DB_PATH = get('EZDATA_LOCAL_DB', str(_API_DIR / 'ezdata_local.db'))
