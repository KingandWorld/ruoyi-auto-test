"""
角色管理模块测试
接口路径：GET/POST/PUT/DELETE /system/role
"""
import yaml
from pathlib import Path
from common.logger import logger
from common.utils import random_str
from testcases.conftest import cleanup_ids

data_path = Path(__file__).resolve().parent.parent / "data" / "role_data.yaml"
with open(data_path, "r", encoding="utf-8") as f:
    td = yaml.safe_load(f)


class TestRoleManager:
    """角色管理 CRUD"""

    def test_list_role(self, base_api):
        """
        查询角色列表
        验证：分页返回 rows + total
        """
        resp = base_api.get("/system/role/list", params=td["list_role"]["params"])
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 200
        assert "rows" in result
        assert result["total"] > 0

        logger.info(f"✅ 角色列表：{result['total']}条")

    def test_create_role(self, base_api, cleanup_ids):
        """
        新增角色 + 自动清理
        验证：创建成功 + 从列表反查 roleId 写入 cleanup_ids 自动删除
        """
        suffix = random_str(8)
        body = {
            "roleName": f"auto_{suffix}",
            "roleKey": f"auto_{suffix}",
            "roleSort": 1,
            "status": "0",
            "menuIds": []
        }

        resp = base_api.post("/system/role", json=body)
        result = resp.json()

        assert result["code"] == 200

        # 从列表反查 roleId（创建响应不返回 roleId）
        list_resp = base_api.get("/system/role/list", params=td["list_role"]["params"])
        rows = list_resp.json()["rows"]
        target = next((r for r in rows if r["roleName"] == body["roleName"]), None)
        if target:
            role_id = target["roleId"]
            cleanup_ids.append(("role", role_id))
            logger.info(f"✅ 创建角色：{body['roleName']} (ID:{role_id})")

    def test_get_role_detail(self, base_api):
        """
        查询角色详情
        验证：先取列表第一个角色，再查详情，data 非空且 roleId 匹配
        """
        list_resp = base_api.get("/system/role/list", params=td["list_role"]["params"])
        list_result = list_resp.json()
        assert list_result["code"] == 200
        assert list_result["total"] > 0, "列表为空，无法测试详情"

        first = list_result["rows"][0]
        role_id = first["roleId"]

        resp = base_api.get(f"/system/role/{role_id}")
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 200
        assert result["data"] is not None
        assert result["data"]["roleId"] == role_id

        logger.info(f"✅ 查询角色详情：{result['data']['roleName']} (ID:{role_id})")

    def test_update_role(self, base_api, cleanup_ids):
        """
        创建临时角色 → 修改角色名称
        验证：修改后 code == 200
        策略：不修改已有角色（admin 角色可能不可修改），自己创建自己改
        """
        suffix = random_str(8)
        body = {
            "roleName": f"temp_upd_{suffix}",
            "roleKey": f"temp_upd_{suffix}",
            "roleSort": 1,
            "status": "0",
            "menuIds": []
        }
        create_resp = base_api.post("/system/role", json=body)
        assert create_resp.json()["code"] == 200

        # 从列表获取完整角色对象（PUT 需要完整结构）
        list_resp = base_api.get("/system/role/list", params=td["list_role"]["params"])
        rows = list_resp.json()["rows"]
        target = next((r for r in rows if r["roleName"] == body["roleName"]), None)
        assert target is not None, "创建角色后未在列表中查到"

        role_id = target["roleId"]
        cleanup_ids.append(("role", role_id))

        # 列表返回的数组字段为 null，PUT 需要空列表不然后端 NPE
        target["menuIds"] = target.get("menuIds") or []
        target["deptIds"] = target.get("deptIds") or []
        target["permissions"] = target.get("permissions") or []

        target["roleName"] = f"{body['roleName']}_updated"

        resp = base_api.put("/system/role", json=target)
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 200

        logger.info(f"✅ 更新角色：{target['roleName']} (ID:{role_id})")

    def test_delete_role(self, base_api):
        """
        创建临时角色 -> 删除 -> 验证
        策略：不删已有角色，自己创建自己删
        说明：创建成功后再从列表查 roleId（创建响应不返回 roleId）
        """
        suffix = random_str(8)
        role_name = f"temp_del_{suffix}"
        create_resp = base_api.post("/system/role", json={
            "roleName": role_name,
            "roleKey": f"temp_del_{suffix}",
            "roleSort": 1,
            "status": "0",
            "menuIds": []
        })
        assert create_resp.json()["code"] == 200, "创建角色失败，无法测试删除"

        # 从列表查询 roleId（创建响应不返回 roleId）
        list_resp = base_api.get("/system/role/list", params=td["list_role"]["params"])
        rows = list_resp.json()["rows"]
        target = next((r for r in rows if r["roleName"] == role_name), None)
        assert target is not None, "创建后未在列表中查到该角色"

        role_id = target["roleId"]
        resp = base_api.delete(f"/system/role/{role_id}")
        assert resp.status_code == 200

        logger.info(f"✅ 删除角色：{role_name} (ID:{role_id})")
