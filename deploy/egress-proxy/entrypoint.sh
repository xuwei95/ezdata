#!/bin/sh
# 沙箱出网代理(tinyproxy):按 SANDBOX_EGRESS_ALLOW 生成域名白名单。
#   SANDBOX_EGRESS_ALLOW=*            → 全放行(不加 filter)
#   SANDBOX_EGRESS_ALLOW=a.com,b.com  → 仅放行这些域名(及其子域),其余拒绝
#   未设置/为空                        → 拒绝一切外网(FilterDefaultDeny + 空白名单)
# 沙箱设 HTTP(S)_PROXY 指向本服务;沙箱本身在 internal 网,直连公网无路由,出网只能经此。
# tinyproxy 已在镜像构建期装好(见 Dockerfile)。
set -eu

CONF=/tmp/tinyproxy.conf
{
  echo 'Port 8888'
  echo 'Listen 0.0.0.0'
  echo 'Timeout 600'
  echo 'Allow 0.0.0.0/0'          # 接受来自沙箱内网的连接
  echo 'ConnectPort 443'          # 允许 HTTPS CONNECT
  echo 'ConnectPort 80'
  echo 'LogLevel Info'
} > "$CONF"

ALLOW="${SANDBOX_EGRESS_ALLOW:-}"
if [ "$ALLOW" = '*' ]; then
  echo '[egress-proxy] SANDBOX_EGRESS_ALLOW=* —— 放行全部外网'
else
  FILTER=/tmp/egress.filter
  : > "$FILTER"
  # 逗号分隔 → 每行一个域名;转义点号作扩展正则(子串匹配,故子域自动覆盖,CDN 友好)
  echo "$ALLOW" | tr ',' '\n' | while IFS= read -r d; do
    d=$(printf '%s' "$d" | tr -d '[:space:]')
    [ -z "$d" ] && continue
    printf '%s\n' "$d" | sed 's/\./\\./g' >> "$FILTER"
  done
  {
    echo "Filter \"$FILTER\""
    echo 'FilterType ere'         # 扩展正则(tinyproxy 1.11+,取代已弃用的 FilterExtended）
    echo 'FilterDefaultDeny Yes'
    echo 'FilterCaseSensitive Off'
  } >> "$CONF"
  echo '[egress-proxy] 白名单域名(其余拒绝):'
  sed 's/^/  - /' "$FILTER" || true
fi

echo '[egress-proxy] 启动 tinyproxy :8888'
exec tinyproxy -d -c "$CONF"
