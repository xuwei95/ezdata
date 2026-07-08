"""连接目录:用内置 sqlite3 存数据源定义(数据管理的落地实现)。

一条记录 = {name, source_type, config(非密钥 dict), secrets(密钥 dict), 时间戳}。
契约对齐 ezdata:resolve(name) -> (source_type, config, secrets 明文) 直接喂给 services。

密钥:本地测试工具,secrets 以 JSON 明文存本机 SQLite 文件(仅本机、不入库、不提交);
如需加密可在此接 cryptography.Fernet,不影响其余代码。
"""

import json
import sqlite3
import threading
from datetime import datetime

_SCHEMA = """
CREATE TABLE IF NOT EXISTS connections (
    name        TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    config      TEXT NOT NULL DEFAULT '{}',
    secrets     TEXT NOT NULL DEFAULT '{}',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
"""


class ConnectionStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = threading.Lock()
        with self._conn() as c:
            c.executescript(_SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ---------- 写 ----------
    def add(self, name: str, source_type: str, config: dict | None = None, secrets: dict | None = None) -> dict:
        now = datetime.now().isoformat(timespec='seconds')
        with self._lock, self._conn() as c:
            exists = c.execute('SELECT 1 FROM connections WHERE name=?', (name,)).fetchone()
            if exists:
                raise ValueError(f'数据源 "{name}" 已存在')
            c.execute(
                'INSERT INTO connections(name, source_type, config, secrets, created_at, updated_at)'
                ' VALUES(?,?,?,?,?,?)',
                (
                    name,
                    source_type,
                    json.dumps(config or {}, ensure_ascii=False),
                    json.dumps(secrets or {}, ensure_ascii=False),
                    now,
                    now,
                ),
            )
        return self.get(name)

    def update(
        self, name: str, *, source_type: str | None = None, config: dict | None = None, secrets: dict | None = None
    ) -> dict:
        cur = self.get(name, mask=False)
        if not cur:
            raise ValueError(f'数据源 "{name}" 不存在')
        st = source_type if source_type is not None else cur['source_type']
        cfg = config if config is not None else cur['config']
        sec = secrets if secrets is not None else cur['secrets']
        now = datetime.now().isoformat(timespec='seconds')
        with self._lock, self._conn() as c:
            c.execute(
                'UPDATE connections SET source_type=?, config=?, secrets=?, updated_at=? WHERE name=?',
                (st, json.dumps(cfg, ensure_ascii=False), json.dumps(sec, ensure_ascii=False), now, name),
            )
        return self.get(name)

    def remove(self, name: str) -> bool:
        with self._lock, self._conn() as c:
            cur = c.execute('DELETE FROM connections WHERE name=?', (name,))
        return cur.rowcount > 0

    # ---------- 读 ----------
    def list(self) -> list[dict]:
        with self._conn() as c:
            rows = c.execute('SELECT * FROM connections ORDER BY name').fetchall()
        return [self._row_to_dict(r, mask=True) for r in rows]

    def get(self, name: str, mask: bool = True) -> dict | None:
        with self._conn() as c:
            r = c.execute('SELECT * FROM connections WHERE name=?', (name,)).fetchone()
        return self._row_to_dict(r, mask=mask) if r else None

    def resolve(self, name: str) -> tuple[str, dict, dict]:
        """→ (source_type, config, secrets 明文),直接喂 ezdata.services。"""
        r = self.get(name, mask=False)
        if not r:
            raise ValueError(f'数据源 "{name}" 不存在')
        return r['source_type'], r['config'], r['secrets']

    @staticmethod
    def _row_to_dict(r: sqlite3.Row, mask: bool) -> dict:
        secrets = json.loads(r['secrets'] or '{}')
        if mask:
            secrets = dict.fromkeys(secrets, '***')
        return {
            'name': r['name'],
            'source_type': r['source_type'],
            'config': json.loads(r['config'] or '{}'),
            'secrets': secrets,
            'created_at': r['created_at'],
            'updated_at': r['updated_at'],
        }
