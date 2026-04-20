#!/bin/bash
# smoke-test.sh — 生产环境冒烟测试
# 用法: ./scripts/smoke-test.sh [基础URL]
set -e

BASE="${1:-http://localhost}"
PASS=0
FAIL=0
RESULTS=()

check() {
    local method="$1" url="$2" expect="$3" data="$4"
    local cmd="curl -sf -o /dev/null -w '%{http_code}'"
    [[ -n "$COOKIE" ]] && cmd="$cmd -b $COOKIE"
    [[ "$method" == "POST" ]] && cmd="$cmd -X POST"
    [[ -n "$data" ]] && cmd="$cmd -H 'Content-Type: application/json' -d '$data'"

    code=$(eval "$cmd $url" 2>/dev/null || echo "000")
    if [[ "$code" == "$expect" ]]; then
        RESULTS+=("PASS $method $url → $code")
        ((PASS++))
    else
        RESULTS+=("FAIL $method $url → $code (expected $expect)")
        ((FAIL++))
    fi
}

echo "==> 冒烟测试: $BASE"
echo "========================================"

# 1. 健康检查（无需认证）
check GET "$BASE/health" 200
check GET "$BASE/ready" 200

# 2. 登录获取 Cookie
echo "==> 登录..."
LOGIN_RESP=$(curl -sf -c /tmp/smoke-cookie.txt \
    -X POST "$BASE/api/v1/auth/login" \
    -H 'Content-Type: application/json' \
    -d "{\"user_id\":\"admin\",\"password\":\"$SMOKE_PASSWORD:-admin123\"}" 2>/dev/null || echo '{"error":"login failed"}')

if echo "$LOGIN_RESP" | grep -q '"id"'; then
    COOKIE="/tmp/smoke-cookie.txt"
    RESULTS+=("PASS POST /api/v1/auth/login → 200")
    ((PASS++))
else
    RESULTS+=("FAIL POST /api/v1/auth/login → $(echo "$LOGIN_RESP" | head -c 80)")
    ((FAIL++))
    COOKIE=""
fi

# 3. 需认证的端点
if [[ -n "$COOKIE" ]]; then
    check GET "$BASE/api/v1/auth/heartbeat" 200

    # 用户管理
    check GET "$BASE/api/v1/users/" 200

    # 校区管理
    check GET "$BASE/api/v1/campuses/" 200

    # 角色管理
    check GET "$BASE/api/v1/roles/" 200

    # 事件上报
    check POST "$BASE/api/v1/events/batch" 200 \
        '[{"event_type":"door_unlock","occurred_at":"2026-01-01T00:00:00Z","device_id":"test","payload":{}}]'

    # 分析看板
    check GET "$BASE/api/v1/analytics/dashboard?range=7d" 200
    check GET "$BASE/api/v1/analytics/usage?range=7d" 200

    # 审计日志
    check GET "$BASE/api/v1/audit/?limit=10" 200

    # 系统配置
    check GET "$BASE/api/v1/config/" 200

    # 密码修改（只测试 422 校验）
    check PUT "$BASE/api/v1/auth/password" 422 \
        '{"old_password":"x","new_password":"short"}'

    # 退出
    check POST "$BASE/api/v1/auth/logout" 200
fi

# 4. 未认证访问应被拒绝
check GET "$BASE/api/v1/users/" 401

# ── 汇总 ──
echo ""
echo "========================================"
for r in "${RESULTS[@]}"; do
    echo "  $r"
done
echo "========================================"
echo "总计: $PASS 通过, $FAIL 失败"

rm -f /tmp/smoke-cookie.txt
[[ $FAIL -eq 0 ]] && echo "✅ 全部通过" || echo "❌ 存在失败"
exit $FAIL
