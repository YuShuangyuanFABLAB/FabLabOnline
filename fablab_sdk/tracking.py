"""事件上报 — 本地 JSONL + 批量上报 + 熔断器"""
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import platformdirs


MAX_LOCAL_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
CIRCUIT_BREAKER_THRESHOLD = 5
CIRCUIT_BREAKER_COOLDOWN = 300  # 5 minutes


class EventReporter:
    """可靠事件上报：本地 JSONL 缓冲 + 批量 API 上报 + 熔断器"""

    def __init__(
        self,
        client: Any,
        local_file: Path | None = None,
        batch_size: int = 10,
    ):
        self._client = client
        if local_file is None:
            data_dir = Path(platformdirs.user_data_dir("fablab-platform"))
            data_dir.mkdir(parents=True, exist_ok=True)
            local_file = data_dir / "pending_events.jsonl"
        self._local_file = local_file
        self._batch: list[dict] = []
        self._batch_size = batch_size
        self._consecutive_failures = 0
        self._circuit_open_until = 0.0

    def track(self, event_type: str, payload: dict) -> None:
        """记录事件：写本地 JSONL + 加入内存 batch，满则 flush"""
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "event_version": 1,
            "event_source": "client",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        self._write_to_local(event)
        self._batch.append(event)
        if len(self._batch) >= self._batch_size:
            self._flush()

    def _write_to_local(self, event: dict) -> None:
        """写入本地 JSONL（status=pending）"""
        try:
            if self._local_file.exists() and self._local_file.stat().st_size > MAX_LOCAL_FILE_SIZE:
                self._rotate_local_file()
            record = json.dumps({"event": event, "status": "pending"}, ensure_ascii=False)
            self._local_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._local_file, "a", encoding="utf-8") as f:
                f.write(record + "\n")
        except Exception:
            pass  # 宁丢事件，不阻塞主线程

    def _rotate_local_file(self) -> None:
        """保留最新一半记录，丢弃旧数据"""
        try:
            lines = self._local_file.read_text(encoding="utf-8").strip().split("\n")
            keep = lines[len(lines) // 2:]
            self._local_file.write_text("\n".join(keep) + "\n", encoding="utf-8")
        except Exception:
            pass

    def _flush(self) -> None:
        """批量上报（带熔断器检查）"""
        now = time.time()
        if self._consecutive_failures >= CIRCUIT_BREAKER_THRESHOLD and now < self._circuit_open_until:
            # 熔断器断开 — 不调用 API
            return

        # 冷却期已过 → 重置
        if self._circuit_open_until > 0 and now >= self._circuit_open_until:
            self._consecutive_failures = 0

        try:
            # 同步调用异步方法
            import asyncio
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # Already in async context — schedule
                asyncio.ensure_future(
                    self._client.api.batch_report(self._batch)
                )
            else:
                asyncio.run(self._client.api.batch_report(self._batch))

            self._consecutive_failures = 0
            self._circuit_open_until = 0
            self._mark_local_sent(self._batch)
            self._compact_local()
            self._batch.clear()
        except Exception:
            self._consecutive_failures += 1
            if self._consecutive_failures >= CIRCUIT_BREAKER_THRESHOLD:
                self._circuit_open_until = time.time() + CIRCUIT_BREAKER_COOLDOWN

    async def replay_pending(self) -> None:
        """启动时重传本地 pending 事件"""
        if not self._local_file.exists():
            return
        try:
            lines = self._local_file.read_text(encoding="utf-8").strip().split("\n")
            pending = []
            for line in lines:
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("status") == "pending":
                    pending.append(record["event"])

            # 分批上报
            for i in range(0, len(pending), self._batch_size):
                batch = pending[i:i + self._batch_size]
                try:
                    await self._client.api.batch_report(batch)
                except Exception:
                    break  # 网络仍不可用，停止重传
        except Exception:
            pass

    def _mark_local_sent(self, events: list[dict]) -> None:
        """将已上报事件的本地记录标记为 sent"""
        if not self._local_file.exists():
            return
        try:
            sent_ids = {e.get("event_id") for e in events}
            lines = self._local_file.read_text(encoding="utf-8").strip().split("\n")
            updated = []
            for line in lines:
                if not line.strip():
                    continue
                record = json.loads(line)
                if record["event"].get("event_id") in sent_ids:
                    record["status"] = "sent"
                updated.append(json.dumps(record, ensure_ascii=False))
            self._local_file.write_text("\n".join(updated) + "\n", encoding="utf-8")
        except Exception:
            pass

    def _compact_local(self) -> None:
        """移除已发送的记录（只保留 pending）"""
        if not self._local_file.exists():
            return
        try:
            lines = self._local_file.read_text(encoding="utf-8").strip().split("\n")
            pending = [line for line in lines if line.strip() and json.loads(line).get("status") == "pending"]
            if len(pending) < len(lines):
                self._local_file.write_text(
                    "\n".join(pending) + "\n" if pending else "",
                    encoding="utf-8",
                )
        except Exception:
            pass
