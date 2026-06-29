#!/bin/sh
# DB 备份:mysqldump / pg_dump → gzip 到 $BACKUP_DIR,按 $BACKUP_KEEP 保留最近 N 份。
# 由 compose 的 ezdata-db-backup sidecar 循环调用,也可手动:
#   docker exec ezdata-db-backup sh /scripts/backup.sh
# 读取环境变量:DB_KIND(mysql|pg) DB_HOST DB_USER DB_PASSWORD DB_NAME BACKUP_DIR BACKUP_KEEP
set -e

DB_KIND="${DB_KIND:-mysql}"
DB_HOST="${DB_HOST:-ezdata-mysql}"
DB_NAME="${DB_NAME:-ezdata}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
BACKUP_KEEP="${BACKUP_KEEP:-7}"

mkdir -p "$BACKUP_DIR"
ts="$(date +%Y%m%d_%H%M%S)"
out="$BACKUP_DIR/ezdata_${DB_KIND}_${ts}.sql.gz"
tmp="$BACKUP_DIR/.dump.$$.sql"

echo "[backup] $(date) -> $out"
# 先 dump 到临时文件以捕获真实退出码(管道到 gzip 会吞掉 mysqldump/pg_dump 的失败)
if [ "$DB_KIND" = "pg" ] || [ "$DB_KIND" = "postgresql" ] || [ "$DB_KIND" = "postgres" ]; then
  export PGPASSWORD="$DB_PASSWORD"
  pg_dump -h "$DB_HOST" -U "${DB_USER:-postgres}" "$DB_NAME" > "$tmp"
else
  mysqldump -h "$DB_HOST" -u "${DB_USER:-root}" -p"$DB_PASSWORD" \
    --single-transaction --routines --triggers --databases "$DB_NAME" > "$tmp"
fi
rc=$?
if [ "$rc" -ne 0 ] || [ ! -s "$tmp" ]; then
  echo "[backup] ERROR: dump 失败(rc=$rc 或空),放弃" >&2
  rm -f "$tmp"
  exit 1
fi
gzip -c "$tmp" > "$out"
rm -f "$tmp"
echo "[backup] ok: $(ls -lh "$out" | awk '{print $5}')"

# 保留最近 N 份,其余删除
ls -1t "$BACKUP_DIR"/ezdata_*.sql.gz 2>/dev/null | tail -n +"$((BACKUP_KEEP + 1))" | while read -r f; do
  echo "[backup] prune $f"
  rm -f "$f"
done
