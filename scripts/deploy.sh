#!/bin/bash
# deploy.sh — 一键部署脚本
# 用法: ./scripts/deploy.sh [分支名] [项目目录]
set -e

BRANCH="${1:-master}"
DIR="${2:-$(cd "$(dirname "$0")/.." && pwd)}"

cd "$DIR"

echo "==> 切换到分支: $BRANCH"
git checkout "$BRANCH"
git pull origin "$BRANCH"

echo "==> 构建镜像"
docker compose build

echo "==> 启动服务（--force-recreate 确保读取最新 .env）"
docker compose up -d --force-recreate

echo "==> 等待服务就绪..."
for i in $(seq 1 30); do
    if curl -sf http://localhost/health > /dev/null 2>&1; then
        echo "==> 部署成功！"
        docker compose ps
        exit 0
    fi
    sleep 2
done

echo "==> 部署失败 — 健康检查超时"
docker compose logs backend --tail 30
exit 1
