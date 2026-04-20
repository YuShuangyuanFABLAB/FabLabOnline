#!/bin/bash
# setup-https.sh — ICP 备案通过后一键配置 HTTPS
# 用法: ./scripts/setup-https.sh <域名> [--dry-run]
#
# 前置条件:
#   1. ICP 备案已通过
#   2. DNS A 记录已指向服务器 IP
#   3. 端口 80 和 443 对外开放
set -e

DOMAIN="${1:?用法: setup-https.sh <域名> [--dry-run]}"
DRY_RUN="${2:-}"
DIR="$(cd "$(dirname "$0")/.." && pwd)"

if [[ "$DRY_RUN" == "--dry-run" ]]; then
    echo "==> DRY RUN 模式 — 只显示将执行的命令"
    CMD="echo >>>"
else
    CMD=""
fi

echo "==> 为 $DOMAIN 配置 HTTPS"

# 1. 安装 acme.sh
if [[ ! -f ~/.acme.sh/acme.sh ]]; then
    echo "==> 安装 acme.sh..."
    $CMD curl https://get.acme.sh | sh
fi

# 2. 创建 webroot 目录
$CMD mkdir -p /var/www/certbot

# 3. 申请证书（webroot 模式）
echo "==> 申请 Let's Encrypt 证书..."
$CMD ~/.acme.sh/acme.sh --issue -d "$DOMAIN" \
    --webroot /var/www/certbot \
    --server letsencrypt \
    --keylength ec-256

# 4. 安装证书
CERT_DIR="$DIR/certs"
$CMD mkdir -p "$CERT_DIR"
$CMD ~/.acme.sh/acme.sh --install-cert -d "$DOMAIN" \
    --ecc \
    --key-file "$CERT_DIR/$DOMAIN.key" \
    --fullchain-file "$CERT_DIR/$DOMAIN.crt" \
    --reloadcmd "docker compose -f $DIR/docker-compose.yml exec -T nginx nginx -s reload"

# 5. 生成 nginx SSL 配置
if [[ "$DRY_RUN" != "--dry-run" ]]; then
    cat > "$DIR/nginx-ssl.conf" <<SSL_EOF
server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate     /etc/nginx/certs/$DOMAIN.crt;
    ssl_certificate_key /etc/nginx/certs/$DOMAIN.key;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 包含原 nginx.conf 的所有 location
    include /etc/nginx/conf.d/locations.conf;
}

server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$host\$request_uri;
}
SSL_EOF
    echo "==> 已生成 nginx-ssl.conf"
fi

echo "==> 完成！手动步骤："
echo "  1. docker-compose.yml 中 nginx 添加 443 端口和证书卷"
echo "  2. 将 nginx-ssl.conf 复制为 nginx 挂载配置"
echo "  3. docker compose up -d --force-recreate nginx"
echo ""
echo "续期脚本: ./scripts/renew-cert.sh $DOMAIN"
