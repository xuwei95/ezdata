#!/bin/sh
# 从备份恢复 DB。⚠️ 会覆盖目标库现有数据,谨慎使用。
# 用法(在 backup sidecar 内,或任一带 mysql/psql 客户端且能连到 DB 的容器):
#   docker exec -e DB_PASSWORD=... ezdata-db-backup sh /scripts/restore.sh /backups/ezdata_mysql_YYYYmmdd_HHMMSS.sql.gz
# 读取环境变量:DB_KIND DB_HOST DB_USER DB_PASSWORD DB_NAME
set -e

FILE="$1"
if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
  echo "用法: restore.sh <备份文件.sql.gz>" >&2
  exit 1
fi

DB_KIND="${DB_KIND:-mysql}"
DB_HOST="${DB_HOST:-ezdata-mysql}"
DB_NAME="${DB_NAME:-ezdata}"

echo "[restore] $FILE -> $DB_KIND@$DB_HOST/$DB_NAME"
if [ "$DB_KIND" = "pg" ] || [ "$DB_KIND" = "postgresql" ] || [ "$DB_KIND" = "postgres" ]; then
  export PGPASSWORD="$DB_PASSWORD"
  gunzip -c "$FILE" | psql -h "$DB_HOST" -U "${DB_USER:-postgres}" "$DB_NAME"
else
  gunzip -c "$FILE" | mysql -h "$DB_HOST" -u "${DB_USER:-root}" -p"$DB_PASSWORD" "$DB_NAME"
fi
echo "[restore] done"
