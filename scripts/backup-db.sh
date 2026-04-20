#!/bin/bash
# backup-db.sh — PostgreSQL 备份 + 轮转
# 用法: ./scripts/backup-db.sh [项目目录]
#
# 已知限制: 备份与数据库在同一台 ECS，磁盘损坏会同时丢失。
# 后续应配置阿里云 OSS 异地存储。
set -e

DIR="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
BACKUP_DIR="${FABLAB_BACKUP_DIR:-/opt/fablab/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/fablab_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[$(date -Iseconds)] 开始备份..."
docker compose -f "$DIR/docker-compose.yml" exec -T db \
  pg_dump -U fablab fablab | gzip > "$BACKUP_FILE"

SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "[$(date -Iseconds)] 备份完成: $BACKUP_FILE ($SIZE)"

# ── 轮转策略 ──
# 日备: 保留 7 天（非 1 号的文件）
find "$BACKUP_DIR" -name "fablab_*_*.sql.gz" -mtime +7 \
  ! -name "fablab_*_01_*.sql.gz" -delete 2>/dev/null || true

# 周备: 保留 4 周（每月 1 号的文件，超过 28 天删除）
find "$BACKUP_DIR" -name "fablab_*_01_*.sql.gz" -mtime +28 -delete 2>/dev/null || true

echo "[$(date -Iseconds)] 轮转完成"
