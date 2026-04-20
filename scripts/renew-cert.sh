#!/bin/bash
# renew-cert.sh — 续期 Let's Encrypt 证书
# 用法: ./scripts/renew-cert.sh <域名>
set -e

DOMAIN="${1:?用法: renew-cert.sh <域名>}"
DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> 续期证书: $DOMAIN"
~/.acme.sh/acme.sh --renew -d "$DOMAIN" --ecc --force

echo "==> 重载 nginx..."
docker compose -f "$DIR/docker-compose.yml" exec -T nginx nginx -s reload

echo "[$(date -Iseconds)] 续期完成"
