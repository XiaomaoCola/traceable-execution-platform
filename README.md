```angular2html
traceable-execution-platform/
├─ README.md
├─ pyproject.toml
├─ docker/
│  ├─ Dockerfile
│  └─ docker-compose.yml                 # postgres + redis + backend（可选再加 minio）
├─ backend/
│  ├─ app/
│  │  ├─ main.py                         # FastAPI app 入口
│  │  ├─ core/
│  │  │  ├─ config.py                    # Settings（环境变量）
│  │  │  ├─ logging.py                   # Logging（日志）
│  │  │  ├─ security.py                  # Security（密码哈希/JWT配置）
│  │  │  └─ dependencies.py              # Dependencies（依赖注入：current_user等）
│  │  ├─ db/
│  │  │  ├─ session.py                   # DB Session（SQLAlchemy会话）
│  │  │  ├─ base.py                      # Base model（Declarative Base）
│  │  │  └─ migrations/                  # Alembic migrations（迁移）
│  │  ├─ models/                         # ORM Models（表结构）
│  │  │  ├─ user.py                      # User
│  │  │  ├─ ticket.py                    # Ticket（工单）
│  │  │  ├─ asset.py                     # Asset（设备/资产）
│  │  │  ├─ run.py                       # Run（执行记录）
│  │  │  └─ artifact.py                  # Artifact（证据/文件元数据）
│  │  ├─ schemas/                        # Pydantic Schemas（输入输出）
│  │  │  ├─ auth.py                      # Token/Login
│  │  │  ├─ user.py
│  │  │  ├─ ticket.py
│  │  │  ├─ asset.py
│  │  │  ├─ run.py
│  │  │  └─ artifact.py
│  │  ├─ api/
│  │  │  ├─ health.py
│  │  │  ├─ auth.py                      # /auth/login /auth/me
│  │  │  ├─ users.py                     # /users（可选：管理端）
│  │  │  ├─ tickets.py                   # /tickets
│  │  │  ├─ assets.py                    # /assets
│  │  │  ├─ runs.py                      # /runs（Run 查询/状态/日志）
│  │  │  └─ artifacts.py                 # /runs/{id}/artifacts 上传/下载
│  │  ├─ services/
│  │  │  ├─ registry.py
│  │  │  ├─ runner.py
│  │  │  ├─ ticket_service.py            # Ticket 业务逻辑（Domain Service）
│  │  │  ├─ asset_service.py
│  │  │  ├─ run_service.py               # Run 创建/完成/失败（写DB）
│  │  │  ├─ artifact_service.py          # Artifact 入库/校验hash/权限
│  │  │  └─ auth_service.py              # Auth（验证/发token）
│  │  ├─ storage/
│  │  │  ├─ state_store.py               # 运行态状态（先内存后Redis）
│  │  │  └─ artifact_store.py            # 文件存储抽象（local/s3/minio）
│  │  ├─ audit/
│  │  │  ├─ events.py                    # Audit Events（审计事件结构）
│  │  │  └─ audit_logger.py              # Audit Log（追加式）
│  │  └─ utils/
│  │     ├─ hashing.py                   # SHA-256 等
│  │     └─ time.py                      # 时间源/NTP（可选）
│  └─ tests/
│     ├─ test_health.py
│     ├─ test_auth.py
│     └─ test_ticket_run_artifact.py
├─ scripts/
├─ script_specs/
└─ run_local.sh
```