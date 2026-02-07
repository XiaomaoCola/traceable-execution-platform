FROM python:3.11-slim
# 这句话的意思是：拿一个已经装好 Python 3.11 的最小 Linux 环境当起点。
# 注意：不是“先起一个容器再装 Python”，而是“直接拿一个已经装好 Python 的 Linux 系统当起点”。
# python:3.11-slim是 Docker 官方提供的一个基础镜像，里面已经有Linux 系统（Debian），Python 3.11，pip等等。

WORKDIR /app
# 以后所有命令（比如 RUN、CMD）默认都在 /app 这个目录下执行。
# 比如在容器里，用刚启动的终端的话，输入 pwd ，就会得到 /app 。

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry==1.7.1

# Copy poetry files
COPY pyproject.toml poetry.lock* /app/
COPY alembic.ini /app/

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY backend/ /app/backend/
COPY scripts/ /app/scripts/
COPY script_specs/ /app/script_specs/

# Create data directory for artifacts
RUN mkdir -p /app/data/artifacts /app/data/audit
# TODO[docker]: 这里GPT说要挂volume，如果不挂 volume，容器删了数据就没了。

ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
# TODO：
# 上面是容器启动后默认执行的命令，完整命令是：
# uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload。
# 不过 --reload 只在开发环境用，以后肯定得改。
