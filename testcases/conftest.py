"""
Pytest 全局配置
================
scope="session" → 整个测试过程只执行一次（登录）
scope="function" → 每个测试用例独立执行（数据清理）
yield 前面 = setup（测试前准备）
yield 后面 = teardown（测试后清理）
"""
import pytest
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from common.logger import logger
from common.base_api import BaseApi

@pytest.fixture(scope="session")
def base_api():
    """
        session 级别 fixture：整个测试过程只登录一次
        """
    api = BaseApi()
    token = api.login()

    assert token is not None, (
        "❌ 登录失败！请检查：\n"
        "  1. RuoYi 服务是否已启动（http://localhost:8080）\n"
        "  2. config.yaml 中的 base_url 和账号密码\n"
        "  3. 登录接口路径是否为 /login"
    )

    logger.info("=" * 50)
    logger.info("✅ 登录成功，开始执行测试")
    logger.info("=" * 50)

    yield api   # 测试用例在这里执行

    logger.info("=" * 50)
    logger.info("🏁 测试全部执行完毕")
    logger.info("=" * 50)

@pytest.fixture(scope="function")
def cleanup_ids(base_api):
    """
        function 级别 fixture：每个测试用例执行前后进行数据清理
    """
    created_ids = []

    yield created_ids

    for resource_type, resource_id in reversed(created_ids):
        try:
            if resource_type == "user":
                base_api.delete(f"/system/user/{resource_id}")
                logger.info(f"[清理] 删除用户：{resource_id}")
            elif resource_type == "role":
                base_api.delete(f"/system/role/{resource_id}")
                logger.info(f"[清理] 删除角色：{resource_id}")
        except Exception as e:
            logger.error(f"[清理失败] {resource_type} {resource_id}：{e}")


