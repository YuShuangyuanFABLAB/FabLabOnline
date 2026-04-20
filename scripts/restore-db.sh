#!/bin/bash
# restore-db.sh — 从备份恢复 PostgreSQL
# 用法: ./scripts/restore-db.sh [备份文件.gz] [--confirm]
#
# ⚠️ 这会覆盖当前数据库！必须传 --confirm 确认。
set -e

BACKUP_FILE="${1:?用法: restore-db.sh <备份文件.sql.gz> --confirm}"
CONFIRM="${2:-}"

if [ "$CONFIRM" != "--confirm" ]; then
    echo "⚠️  这将覆盖当前数据库！请加 --confirm 确认"
    echo "用法: $0 <备份文件.sql.gz> --confirm"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "错误: 文件不存在: $BACKUP_FILE"
    exit 1
fi

DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "⚠️  即将从 $BACKUP_FILE 恢复数据库"
echo "按 Ctrl+C 取消，5 秒后开始..."
sleep 5

gunzip -c "$BACKUP_FILE" | docker compose -f "$DIR/docker-compose.yml" exec -T db \
  psql -U fablab fablab

echo "[$(date -Iseconds)] 恢复完成"
