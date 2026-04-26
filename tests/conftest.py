"""顶层 conftest：全局 fixture，供 unit_tests/ 和 integration_tests/ 共用。

重构说明：
  原来 audit_logger、security 等模块在 import 时就调用 settings = Settings()，
  CI 没有 .env 就崩。重构为 get_settings() 后，Settings() 推迟到首次调用，
  import 本身无副作用，conftest 不再需要 os.environ.setdefault 打补丁。

  session.py / artifact_store.py / state_store.py 仍有模块级单例，
  但当前测试不 import 它们，暂时不影响。未来补这几个模块的测试时，
  在 integration_tests/conftest.py 里配置真实 DB 即可。

未来集成测试需要 FastAPI TestClient 时，在这里加 app / async_client fixture。
"""
