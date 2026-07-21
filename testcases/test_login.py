"""
登录模块接口测试
================
测试策略：
  - 正向 1 条：正确账号密码登录成功
  - 异常 4 条：错误密码、空用户名、空密码、空全部
  - 方法校验 1 条：GET 请求登录（预期 405）
"""
from pathlib import Path
import yaml

data_path = Path(__file__).resolve().parent.parent / "data" / "login_data.yaml"
with open(data_path, "r", encoding="utf-8") as f:
    td = yaml.safe_load(f)

class TestLogin:
    """登录模块测试"""

    def test_valid_success(self, base_api):
        """
        正向用例：正确账号密码登录成功
        断言四层：状态码 -> 业务code -> 业务msg -> token存在性
        """
        data = td["valid_login"]
        resp = base_api.post("/login", json=data["body"])

        # 第一层：HTTP 状态码
        assert resp.status_code == data["excepted"]["status_code"]
        # 第二层：业务状态码
        result = resp.json()
        assert result["code"] == data["excepted"]["code"]
        # 第三层：业务提示信息
        assert result["msg"] == data["excepted"]["msg"]
        # 第四层：token 存在性
        assert "token" in result

        print("登录成功")

    def test_invalid_password(self, base_api):
        """异常：错误密码"""
        data = td["invalid_password"]
        resp = base_api.post("/login", json=data["body"])
        result = resp.json()

        # RuoYi 返回 HTTP 200 但业务 code 是 500
        assert resp.status_code == data["excepted"]["status"]
        assert result["code"] == data["excepted"]["code"]
        assert data["excepted"]["msg_contains"] in result.get("msg", "")

        print("错误密码，测试通过")

    def test_empty_username(self, base_api):
        """异常：空用户名"""
        data = td["empty_username"]
        resp = base_api.post("/login", json=data["body"])
        result = resp.json()

        # 空用户名不应该登录成功
        assert result.get("code") != 200, f"空用户名竟然登录成功: {result}"

        print("空用户名，测试通过")
    def test_empty_password(self, base_api):
        """异常：空密码"""
        data = td["empty_password"]
        resp = base_api.post("/login", json=data["body"])
        result = resp.json()

        # 空密码不应该登录成功
        assert result.get("code") != 200, f"空密码竟然登录成功: {result}"

        print("空密码，测试通过")
    def test_empty_both(self, base_api):
        """异常：空用户名密码"""
        data = td["empty_both"]
        resp = base_api.post("/login", json=data["body"])
        result = resp.json()

        # 空用户名密码不应该登录成功
        assert result.get("code") != 200, f"空用户名和密码竟然登录成功: {result}"

        print("空用户名和密码，测试通过")
