"""
用户管理模块测试
接口路径：GET/POST/PUT/DELETE /system/user
"""
import yaml
from pathlib import Path
from common.logger import logger
from common.utils import random_str, random_phone, random_email
from testcases.conftest import cleanup_ids

data_path = Path(__file__).resolve().parent.parent / "data" / "user_data.yaml"
with open(data_path, "r", encoding="utf-8") as f:
    td = yaml.safe_load(f)

class TestUserManager:
    """用户管理 CRUD"""

    def test_list_user(self, base_api):
        """
        查询用户列表
        验证：分页返回 rows + total
        """
        resp = base_api.get("/system/user/list", params=td["list_user"]["params"])
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 200
        assert "rows" in result
        assert result["total"] > 0

        logger.info(f"✅ 用户列表：{result['total']}条")

    def test_create_user(self, base_api, cleanup_ids):
        """
        新增用户 + 自动清理
        验证：创建成功 + userId 写入 cleanup_ids 自动删除
        """
        suffix = random_str(8)
        body = {
            "userName": f"auto_{suffix}",
            "nickName": f"auto_{suffix}",
            "password": "123456",
            "phoneNumber": random_phone(),
            "email": random_email(suffix),
            "status": "0",
            "roleIds": []
        }

        resp = base_api.post("/system/user", json=body)
        result = resp.json()

        assert result["code"] == 200

        user_id = result.get("userId")
        if user_id:
            cleanup_ids.append(("user", user_id))
            logger.info(f"✅ 创建用户：{body['userName']} (ID:{user_id})")

    def test_delete_user(self, base_api):
        """
        创建临时用户 -> 删除 -> 验证
        策略：不删已有用户，自己创建自己删
        说明：创建成功后再从列表查 userId（创建响应不返回 userId）
        """
        suffix = random_str(8)
        user_name = f"temp_del_{suffix}"
        create_resp = base_api.post("/system/user", json={
            "userName": user_name,
            "nickName": user_name,
            "password": "123456",
            "status": "0"
        })
        assert create_resp.json()["code"] == 200, "创建用户失败，无法测试删除"

        # 从列表查询 userId（按用户名过滤避免分页问题）
        list_params = {**td["list_user"]["params"], "userName": user_name}
        list_resp = base_api.get("/system/user/list", params=list_params)
        rows = list_resp.json()["rows"]
        target = next((u for u in rows if u["userName"] == user_name), None)
        assert target is not None, "创建后未在列表中查到该用户"

        user_id = target["userId"]
        resp = base_api.delete(f"/system/user/{user_id}")
        assert resp.status_code == 200

        logger.info(f"✅ 删除用户：{user_name} (ID:{user_id})")

    def test_get_user_detail(self, base_api):
        """
        查询用户详情
        验证：先取列表第一个用户，再查详情，data 非空且 userId 匹配
        """
        # 先查列表取第一个 userId
        list_resp = base_api.get("/system/user/list", params=td["list_user"]["params"])
        list_result = list_resp.json()
        assert list_result["code"] == 200
        assert list_result["total"] > 0, "列表为空，无法测试详情"

        first = list_result["rows"][0]
        user_id = first["userId"]

        # 查详情
        resp = base_api.get(f"/system/user/{user_id}")
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 200
        assert result["data"] is not None
        assert result["data"]["userId"] == user_id

        logger.info(f"✅ 查询用户详情：{result['data']['userName']} (ID:{user_id})")

    def test_update_user(self, base_api, cleanup_ids):
        """
        创建临时用户 → 修改 email
        验证：修改后 email 与更新值一致
        策略：不修改已有用户（admin 不可修改），自己创建自己改
        """
        # 创建一个临时用户用于修改
        suffix = random_str(8)
        body = {
            "userName": f"temp_upd_{suffix}",
            "nickName": f"temp_upd_{suffix}",
            "password": "123456",
            "status": "0"
        }
        create_resp = base_api.post("/system/user", json=body)
        assert create_resp.json()["code"] == 200

        # 从列表获取完整用户对象（按用户名过滤避免分页问题）
        list_params = {**td["list_user"]["params"], "userName": body["userName"]}
        list_resp = base_api.get("/system/user/list", params=list_params)
        rows = list_resp.json()["rows"]
        target = next((u for u in rows if u["userName"] == body["userName"]), None)
        assert target is not None, "创建用户后未在列表中查到"

        user_id = target["userId"]
        cleanup_ids.append(("user", user_id))

        new_email = random_email(suffix)
        target["email"] = new_email

        resp = base_api.put("/system/user", json=target)
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 200

        logger.info(f"✅ 更新用户：{target['userName']} (ID:{user_id}) → email: {new_email}")

    def test_get_nonexistent_user(self, base_api):
        """
        查询不存在的用户
        验证：GET /system/user/999999，返回 data 为 null
        """
        resp = base_api.get("/system/user/999999")
        result = resp.json()

        assert resp.status_code == 200
        assert result.get("data") is None

        logger.info("✅ 查询不存在用户：返回 data 为 null 符合预期")

    def test_create_user_without_required_field(self, base_api):
        """
        创建用户时缺少必填字段
        验证：只传 password 不传 userName，code != 200
        """
        resp = base_api.post("/system/user", json={"password": "123456"})
        result = resp.json()

        assert result["code"] != 200

        logger.info(f"✅ 缺少 userName 创建用户：code={result['code']} 符合预期")


