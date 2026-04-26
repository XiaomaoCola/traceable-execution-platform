"""顶层 conftest：全局 fixture，供 unit_tests/ 和 integration_tests/ 共用。

当前只做一件事：在任何 app 模块被导入之前，确保 settings 能正常加载。
项目有 .env 文件，本地跑测试不需要额外配置。

未来集成测试需要 FastAPI TestClient 时，在这里加 app / async_client fixture。
"""
