FROM python:3.11-slim

WORKDIR /app

COPY 后端/requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

COPY 后端/ .

# 启动时：尝试 alembic 迁移，失败则由 init_db fallback 建表；然后种子数据 + 启动服务
# 注意：workers=1 因为 asyncio.Queue 是进程内队列，多 worker 会导致事件丢失
CMD ["sh", "-c", "alembic upgrade head || true; python init_db.py && uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1"]
