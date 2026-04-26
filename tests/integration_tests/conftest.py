"""integration_tests 层的 conftest：占位，待集成测试补充时填充。

集成测试需要真实数据库。推荐方案：
  - 本地跑：docker compose up postgres，用 .env.test 覆盖 DATABASE_URL
  - CI：testcontainers-python 自动起 postgres 容器

在这里加的 fixture 示例（未来用）：

    @pytest.fixture(scope="session")
    async def test_engine():
        engine = create_async_engine(TEST_DATABASE_URL)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield engine
        await engine.dispose()
"""
