#!/usr/bin/env python3
"""
为某个部署环境生成强随机密钥,并填进 app env 文件与 compose 根 .env。

用法:
    python deploy/gen-secrets.py --env dockermy            # 默认从 api/.env.dockermy.example 生成 api/.env.dockermy
    python deploy/gen-secrets.py --env dockerpg --force    # 覆盖已存在文件

产物:
    1. api/.env.<env>     —— 由 .example 模板复制,填入随机 JWT/数据加密/传输RSA/各口令
    2. <repo>/.env        —— compose 层基础设施口令(DB/Redis/ES/MinIO/Sandbox),与 app env 对齐

注意:这是“首次部署/轮换”工具。对已初始化且有数据卷的库,轮换 DB/Redis/ES/MinIO 口令需同步改库,
否则连不上;此脚本默认整套重新随机,适合全新部署。只想补 DATA_ENCRYPT_KEY 可手动加单行。
"""
import argparse
import os
import re
import secrets
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _rsa_keypair() -> tuple[str, str]:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    priv = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    pub = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    # .env 单行存储:换行转义为 \n
    return pub.replace('\n', '\\n'), priv.replace('\n', '\\n')


def _gen() -> dict[str, str]:
    from cryptography.fernet import Fernet

    pw = lambda: secrets.token_urlsafe(18)  # noqa: E731
    db_pw, redis_pw, es_pw, minio_pw = pw(), pw(), pw(), pw()
    pub, priv = _rsa_keypair()
    return {
        # 应用层(写进 api/.env.<env>)
        'JWT_SECRET_KEY': secrets.token_hex(32),
        'DATA_ENCRYPT_KEY': Fernet.generate_key().decode(),
        'DB_PASSWORD': db_pw,
        'REDIS_PASSWORD': redis_pw,
        'TASK_ES_PASSWORD': es_pw,
        'RAG_VECTOR_PASSWORD': es_pw,
        'S3_SECRET_KEY': minio_pw,
        'SANDBOX_BEARER_KEY': 'sbx-' + secrets.token_urlsafe(24),
        'TRANSPORT_CRYPTO_PUBLIC_KEY': pub,
        'TRANSPORT_CRYPTO_PRIVATE_KEY': priv,
        # 供 compose 根 .env(基础设施容器口令),与上面对齐
        '_DB_PASSWORD': db_pw,
        '_REDIS_PASSWORD': redis_pw,
        '_ELASTIC_PASSWORD': es_pw,
        '_MINIO_ROOT_PASSWORD': minio_pw,
    }


def _replace_kv(text: str, key: str, value: str) -> str:
    """替换 `KEY = '...'` 行的值;不存在则追加。"""
    pat = re.compile(rf"^(\s*{re.escape(key)}\s*=\s*).*$", re.MULTILINE)
    if pat.search(text):
        return pat.sub(lambda m: f"{key} = '{value}'", text, count=1)
    return text.rstrip('\n') + f"\n{key} = '{value}'\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--env', default='dockermy', help='部署环境名(dockermy/dockerpg/prod)')
    ap.add_argument('--force', action='store_true', help='覆盖已存在的 app env / 根 .env')
    args = ap.parse_args()

    app_env = os.path.join(REPO, 'api', f'.env.{args.env}')
    example = app_env + '.example'
    root_env = os.path.join(REPO, '.env')

    if os.path.exists(app_env) and not args.force:
        print(f'已存在 {app_env}(用 --force 覆盖)', file=sys.stderr)
        return 1
    if not os.path.exists(example):
        print(f'缺少模板 {example}', file=sys.stderr)
        return 1

    s = _gen()
    text = open(example, encoding='utf-8').read()
    # 去掉模板头两行警示注释
    text = re.sub(r'^# ⚠️.*\n# .*\n\n', '', text, count=1)
    for k in (
        'JWT_SECRET_KEY', 'DATA_ENCRYPT_KEY', 'DB_PASSWORD', 'REDIS_PASSWORD',
        'TASK_ES_PASSWORD', 'RAG_VECTOR_PASSWORD', 'S3_SECRET_KEY', 'SANDBOX_BEARER_KEY',
        'TRANSPORT_CRYPTO_PUBLIC_KEY', 'TRANSPORT_CRYPTO_PRIVATE_KEY',
    ):
        text = _replace_kv(text, k, s[k])
    open(app_env, 'w', encoding='utf-8').write(text)
    print(f'写入 {app_env}')

    # compose 根 .env(基础设施容器口令 + 沙箱 key,与 app env 对齐)
    if os.path.exists(root_env) and not args.force:
        print(f'已存在 {root_env},跳过(用 --force 覆盖);请手动核对口令一致', file=sys.stderr)
    else:
        root = (
            '# compose 基础设施口令(由 deploy/gen-secrets.py 生成,与 api/.env.<env> 对齐)。已 gitignore。\n'
            f'DB_PASSWORD={s["_DB_PASSWORD"]}\n'
            f'REDIS_PASSWORD={s["_REDIS_PASSWORD"]}\n'
            f'ELASTIC_PASSWORD={s["_ELASTIC_PASSWORD"]}\n'
            f'MINIO_ROOT_PASSWORD={s["_MINIO_ROOT_PASSWORD"]}\n'
            f'SANDBOX_BEARER_KEY={s["SANDBOX_BEARER_KEY"]}\n'
        )
        open(root_env, 'w', encoding='utf-8').write(root)
        print(f'写入 {root_env}')

    print('完成。请妥善保管,勿提交进仓库。')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
