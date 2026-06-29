#!/usr/bin/env sh
# 生成某部署环境的强随机密钥(JWT/数据加密/传输RSA/各口令),填进 api/.env.<env> 与根 .env。
# 用法: deploy/gen-secrets.sh --env dockermy [--force]
# 仅作 python 实现的薄封装,逻辑见 deploy/gen-secrets.py。
set -e
DIR="$(cd "$(dirname "$0")/.." && pwd)"
exec python "$DIR/deploy/gen-secrets.py" "$@"
