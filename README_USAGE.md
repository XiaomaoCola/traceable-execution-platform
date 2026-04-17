# Traceable Execution Platform - Usage Guide

## 🎯 项目概述

这是一个**可追溯、可还原、受控执行**的后端平台，用于管理工单和执行记录，确保操作的完整审计链。

### 核心设计原则

- **Ticket**：人的承诺（我要做这个事）
- **Run**：系统的承诺（我确实做/验证/记录了某个过程）
- **Artifact**：结果的证据（配置、日志、截图、hash）
- **Audit**：不可抵赖的流水（谁在什么时候做了什么）

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装 Poetry（Python 依赖管理工具）
pip install poetry

# 安装项目依赖
poetry install
```

### 2. 使用 Docker Compose（推荐）

```bash
# 启动所有服务（PostgreSQL + Redis + Backend）
cd docker
docker-compose up -d

# 查看日志
docker-compose logs -f backend

# 停止服务
docker-compose down
```

### 3. 本地开发模式

```bash
# 确保 PostgreSQL 和 Redis 正在运行
# 然后使用本地启动脚本
bash run_local.sh
```

### 4. 初始化数据库

```bash
# 创建数据库表
poetry run alembic upgrade head

# 初始化示例数据（创建管理员和员工用户）
poetry run python scripts/init_db.py
```

默认用户：
- 管理员: `username=admin, password=admin123`
- 员工: `username=employee, password=employee123`

### 5. 访问 API 文档

启动后访问：
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## 📋 典型工作流

### ProofRun 工作流（证据校验型）

```
1. 员工创建工单
   POST /api/v1/tickets
   {
     "title": "安装工厂交换机",
     "description": "在工厂 A 安装新交换机并上传配置",
     "asset_id": 3
   }

2. 员工创建 ProofRun
   POST /api/v1/runs
   {
     "run_type": "proof",
     "ticket_id": 1,
     "script_id": "proof.file_hash"
   }

3. 员工上传配置文件作为证据
   POST /api/v1/artifacts?run_id=1
   [文件上传]

4. 系统自动执行验证
   - 校验文件 hash
   - 验证格式
   - 生成报告

5. 查看验证结果
   GET /api/v1/runs/1
```

### 示例代码

```bash
# 运行示例脚本
poetry run python scripts/example_proof_run.py
```

## 🏗️ 项目结构

```
traceable-execution-platform/
├── backend/app/
│   ├── api/              # API 路由
│   ├── core/             # 核心配置（config, security, logging）
│   ├── db/               # 数据库（session, models, migrations）
│   ├── models/           # ORM 模型（User, Ticket, Run, Artifact）
│   ├── schemas/          # Pydantic schemas（API 输入输出）
│   ├── services/         # 业务逻辑（auth, ticket, run, artifact）
│   ├── storage/          # 存储层（artifact_store, state_store）
│   ├── audit/            # 审计日志（events, audit_logger）
│   └── utils/            # 工具函数
├── docker/               # Docker 配置
├── scripts/              # 工具脚本
└── script_specs/         # 注册的脚本规范（未来用于 ActionRun）
```

## 🔐 权限模型

### 角色

- **employee**（员工）：
  - 创建工单
  - 上传 artifact
  - 发起 ProofRun
  - 查看自己的工单和 run

- **admin**（管理员）：
  - 所有 employee 权限
  - 审批工单
  - 发起 ActionRun
  - 查看所有审计日志
  - 管理资产和用户

### 审批流程

- **ProofRun**：不需要审批（只是验证）
- **ActionRun**：必须管理员审批（因为会对资产产生变更）

## 📊 审计日志

所有操作都会记录到审计日志（append-only）：

```
data/audit/audit_2024-01-20.jsonl         # 机器可读（JSON Lines）
data/audit/audit_readable_2024-01-20.txt  # 人类可读
```

审计事件包括：
- 用户登录/登出
- 工单创建/更新/审批
- Run 创建/执行/完成
- Artifact 上传/下载/验证

## 🔧 配置选项

环境变量（`.env` 文件）：

```bash
# 数据库
DATABASE_URL=postgresql://user:pass@localhost:5432/db

# Redis
REDIS_URL=redis://localhost:6379/0

# 安全
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 存储
ARTIFACT_STORAGE_TYPE=local  # local, minio, s3
ARTIFACT_STORAGE_PATH=./data/artifacts

# 审计
AUDIT_LOG_PATH=./data/audit

# 执行
RUN_TIMEOUT_SECONDS=300
MAX_ARTIFACT_SIZE_MB=100
```

## 🧪 开发和测试

```bash
# 运行测试
poetry run pytest

# 代码格式化
poetry run black backend/

# 代码检查
poetry run ruff check backend/

# 创建新的数据库迁移
poetry run alembic revision --autogenerate -m "描述"

# 应用迁移
poetry run alembic upgrade head
```

## 🚧 未来扩展

### ActionRun 实现计划

1. 脚本隔离执行（Docker sandbox）
2. 超时和资源限制
3. 脚本注册表（whitelist）
4. 输出 artifacts 自动收集
5. 前后配置 diff

### MinIO/S3 存储

当需要多机部署或大量文件时，可切换到对象存储：

```python
# backend/app/core/config.py
ARTIFACT_STORAGE_TYPE=minio
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...
```

## 📞 问题排查

### 常见问题

1. **数据库连接失败**
   - 检查 PostgreSQL 是否运行
   - 检查 `DATABASE_URL` 配置

2. **Artifact 上传失败**
   - 检查 `data/artifacts` 目录权限
   - 检查文件大小是否超过 `MAX_ARTIFACT_SIZE_MB`

3. **Run 执行失败**
   - 查看 `GET /api/v1/runs/{id}` 的 `stderr_log`
   - 检查审计日志

## 📝 API 概览

### 认证
- `POST /auth/login` - 登录
- `POST /auth/register` - 注册
- `GET /auth/me` - 当前用户信息

### 工单
- `POST /tickets` - 创建工单
- `GET /tickets` - 列出工单
- `GET /tickets/{id}` - 获取工单详情
- `PATCH /tickets/{id}` - 更新工单
- `POST /tickets/{id}/approve` - 审批工单（admin）

### 资产
- `POST /assets` - 创建资产
- `GET /assets` - 列出资产
- `GET /assets/{id}` - 获取资产详情

### Run
- `POST /runs` - 创建并执行 run
- `GET /runs` - 列出 runs
- `GET /runs/{id}` - 获取 run 详情（含日志）

### Artifact
- `POST /artifacts` - 上传 artifact
- `GET /artifacts/{id}` - 获取 artifact 元数据
- `GET /artifacts/{id}/download` - 下载 artifact
- `GET /artifacts/run/{run_id}` - 列出 run 的所有 artifacts

---

**祝使用愉快！如有问题，请查看审计日志或联系管理员。**
