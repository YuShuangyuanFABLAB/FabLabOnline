"""Task C: RateLimitMiddleware 内存泄漏 — 过期 key 清理"""
import time
import pytest

from api.rate_limit import RateLimitMiddleware


class TestRateLimitMemoryCleanup:
    """过期条目应从 _hits 字典中移除，防止内存泄漏"""

    def test_expired_key_removed_when_reaccessed(self):
        """窗口过期后重新访问 key，_hits[key] 中的过期记录应被清理且只保留新请求"""
        middleware = RateLimitMiddleware(None, requests_per_minute=5, window_seconds=1)
        hits = middleware._hits

        # 第一次请求
        middleware._is_limited("1.1.1.1")
        assert len(hits["1.1.1.1"]) == 1

        # 等待窗口过期
        time.sleep(1.1)

        # 再次访问同一 key — 旧记录应被清理，只保留新请求
        middleware._is_limited("1.1.1.1")
        assert len(hits["1.1.1.1"]) == 1  # 只有新请求，旧记录被清理

    def test_limited_key_still_blocks(self):
        """限流逻辑在清理后仍应正常工作"""
        middleware = RateLimitMiddleware(None, requests_per_minute=2, window_seconds=60)

        assert middleware._is_limited("1.1.1.1") is False  # 第1次
        assert middleware._is_limited("1.1.1.1") is False  # 第2次
        assert middleware._is_limited("1.1.1.1") is True   # 第3次 → 限流

    def test_active_key_not_cleaned(self):
        """未过期的 key 不应被清理"""
        middleware = RateLimitMiddleware(None, requests_per_minute=10, window_seconds=60)
        middleware._is_limited("active_ip")
        middleware._is_limited("active_ip")
        assert len(middleware._hits["active_ip"]) == 2
