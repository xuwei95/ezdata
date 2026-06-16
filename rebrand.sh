#!/usr/bin/env bash
# ============================================================================
# rebrand.sh — 去品牌化：把「牌子 + 库名」等安全位置改成你的项目名。
#
# 只改「显示用的牌子」和「需成套对齐的库名」这类安全位置；
# 故意不碰第三档内部标识符（module_* 包名 / 权限串 / 路由前缀 / 表名 / SQL 路径），
# 改那些会牵连成百上千处，且用户根本看不到。
#
# 用法：
#   ./rebrand.sh <项目名> [显示名]            # 预览(dry-run)，不写入
#   ./rebrand.sh <项目名> [显示名] --apply    # 实际写入
# 例：
#   ./rebrand.sh tmplate                      # 项目名=tmplate，显示名也=tmplate
#   ./rebrand.sh tmplate "Tmplate 管理平台" --apply
# ============================================================================
set -euo pipefail

PROJECT="${1:?用法: ./rebrand.sh <项目名(小写slug)> [显示名] [--apply]}"
shift || true
TITLE="$PROJECT"
APPLY=0
for a in "$@"; do
  case "$a" in
    --apply) APPLY=1 ;;
    *) TITLE="$a" ;;
  esac
done
DB="$PROJECT"                       # 数据库名 = 项目名
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

changed=0
# 对单个文件套用一组 perl -pe 表达式；diff 出变化；--apply 时才真正写回。
# 用 perl(非 sed)：git-bash 的 sed 会把 CRLF 整文件归一成 LF，造成「整文件都变」的假象；
# perl 只动命中的字节，行尾 CRLF/LF 原样保留。所有到行尾的匹配用 [^\r\n]* 而非 .*，对 CRLF 也安全。
edit() {
  local f="$1"; shift
  if [ ! -f "$f" ]; then echo "  (跳过·不存在) $f"; return 0; fi
  local tmp; tmp="$(mktemp)"
  perl -pe "$@" "$f" > "$tmp"
  if diff -q "$f" "$tmp" >/dev/null 2>&1; then
    rm -f "$tmp"
  else
    echo "── $f"
    diff -u "$f" "$tmp" | grep -E '^[-+][^-+]' | sed 's/^/    /' || true
    changed=$((changed + 1))
    if [ "$APPLY" = 1 ]; then mv "$tmp" "$f"; else rm -f "$tmp"; fi
  fi
}

echo "================================================================"
echo "  项目名(slug) : $PROJECT      库名: $DB"
echo "  显示名(title): $TITLE"
echo "  模式         : $([ "$APPLY" = 1 ] && echo '写入 (--apply)' || echo '预览 dry-run（不写入）')"
echo "================================================================"

echo ""; echo "【1】后端 .env（APP_NAME / DB_DATABASE / LOG_SERVICE_NAME）"
for f in ruoyi-fastapi-backend/.env.dev ruoyi-fastapi-backend/.env.prod \
         ruoyi-fastapi-backend/.env.dockermy ruoyi-fastapi-backend/.env.dockerpg; do
  edit "$f" "s/^APP_NAME = [^\r\n]*/APP_NAME = '$TITLE'/; s/^DB_DATABASE = [^\r\n]*/DB_DATABASE = '$DB'/; s/^LOG_SERVICE_NAME = [^\r\n]*/LOG_SERVICE_NAME = '$PROJECT-backend'/"
done

echo ""; echo "【2】后端 config/env.py（app_name 默认值）"
edit ruoyi-fastapi-backend/config/env.py "s/app_name: str = '[^']*'/app_name: str = '$TITLE'/"

echo ""; echo "【3】前端 .env.*（VITE_APP_TITLE 浏览器/侧边栏标题）"
for f in ruoyi-fastapi-frontend/.env.development ruoyi-fastapi-frontend/.env.docker \
         ruoyi-fastapi-frontend/.env.production ruoyi-fastapi-frontend/.env.staging; do
  edit "$f" "s/^VITE_APP_TITLE = [^\r\n]*/VITE_APP_TITLE = $TITLE/"
done

echo ""; echo "【4】App（manifest 应用名 / package.json 包名）"
edit ruoyi-fastapi-app/src/manifest.json "s/\"name\": \"RuoYi-FastAPI移动端\"/\"name\": \"$TITLE\"/"
edit ruoyi-fastapi-app/package.json       "s/\"name\": \"ruoyi-fastapi-app\"/\"name\": \"$PROJECT-app\"/"

echo ""; echo "【5】docker-compose 库名（与 DB_DATABASE 对齐，保留行尾注释）"
edit docker-compose.dev.yml "s/MYSQL_DATABASE: ruoyi-fastapi/MYSQL_DATABASE: $DB/"
edit docker-compose.my.yml  "s/MYSQL_DATABASE: ruoyi-fastapi/MYSQL_DATABASE: $DB/"
edit docker-compose.pg.yml  "s/POSTGRES_DB: ruoyi-fastapi/POSTGRES_DB: $DB/"

echo ""
echo "================================================================"
echo "  共 $changed 个文件 $([ "$APPLY" = 1 ] && echo '已修改' || echo '将被修改')"
echo "  故意未改(第三档·内部标识符,改了会牵连别处)："
echo "    · Python 包目录 module_admin / module_*"
echo "    · 权限串 system:* / 菜单 perms / API 路由前缀 /system/*"
echo "    · 数据表名、SQL 文件名与挂载路径"
echo "    · docker 容器名/网络名/镜像名、CLI 命令名 ruoyi（如需,见 README 第二档②③手动改）"
echo "================================================================"
[ "$APPLY" = 1 ] || echo "（预览模式,未写入。确认无误后加 --apply 实际执行。）"
