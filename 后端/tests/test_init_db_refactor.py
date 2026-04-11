"""测试 init_db 重构 + Alembic — H3 TDD"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call


class TestSeedDataSkipsWhenPopulated:
    """seed_data 在已有数据时跳过"""

    @pytest.mark.asyncio
    async def test_seed_skips_when_tenants_exist(self):
        """tenants 表有数据时 seed_data 跳过"""
        from init_db import seed_data

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5  # 已有 5 条 tenant
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("init_db.async_session") as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            await seed_data()

            # 只执行了一次 SELECT COUNT（不做 INSERT）
            assert mock_db.execute.call_count == 1
            mock_db.commit.assert_not_called()


class TestInitDbFallback:
    """init() 在无 Alembic 时 fallback 到 create_tables"""

    @pytest.mark.asyncio
    async def test_init_creates_tables_when_no_alembic(self):
        """无 alembic_version 表时自动调 create_tables"""
        from init_db import init

        async def mock_execute(stmt):
            # 模拟 alembic_version 表不存在
            raise Exception("relation \"alembic_version\" does not exist")

        mock_conn = AsyncMock()
        mock_conn.execute = mock_execute
        mock_conn.run_sync = AsyncMock()

        mock_db = AsyncMock()
        mock_result_count = MagicMock()
        mock_result_count.scalar.return_value = 5  # 已有数据，seed 跳过
        mock_db.execute = AsyncMock(return_value=mock_result_count)

        with patch("init_db.engine") as mock_engine, \
             patch("init_db.create_tables", new_callable=AsyncMock) as mock_create, \
             patch("init_db.seed_data", new_callable=AsyncMock) as mock_seed, \
             patch("init_db.async_session") as mock_session:
            mock_engine.begin = MagicMock(return_value=mock_conn)
            mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_conn.__aexit__ = AsyncMock(return_value=False)
            mock_engine.begin.return_value = mock_conn

            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            await init()

            # create_tables 应该被调用（fallback）
            mock_create.assert_called_once()
            mock_seed.assert_called_once()

    @pytest.mark.asyncio
    async def test_init_skips_create_tables_when_alembic_exists(self):
        """有 alembic_version 表时跳过 create_tables"""
        from init_db import init

        mock_conn = AsyncMock()
        mock_version_result = MagicMock()
        mock_version_result.scalar.return_value = 1  # alembic_version 有记录
        mock_conn.execute = AsyncMock(return_value=mock_version_result)

        with patch("init_db.engine") as mock_engine, \
             patch("init_db.create_tables", new_callable=AsyncMock) as mock_create, \
             patch("init_db.seed_data", new_callable=AsyncMock) as mock_seed:
            mock_engine.begin.return_value = mock_conn
            mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_conn.__aexit__ = AsyncMock(return_value=False)

            await init()

            # create_tables 不应该被调用
            mock_create.assert_not_called()
            mock_seed.assert_called_once()
