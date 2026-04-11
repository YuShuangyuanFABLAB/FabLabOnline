FROM python:3.11-slim

WORKDIR /app

COPY 后端/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY 后端/ .

# 启动时先运行数据库迁移和种子数据，再启动服务
CMD ["sh", "-c", "alembic upgrade head && python init_db.py && uvicorn main:app --host 0.0.0.0 --port 8000"]
