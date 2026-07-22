"""
部门管理模块测试
接口路径：GET/POST/PUT/DELETE /system/dept
注意：部门列表返回 tree 结构（data），不是分页的 rows
"""
import yaml
from pathlib import Path
from common.logger import logger
from common.utils import random_str
from testcases.conftest import cleanup_ids

data_path = Path(__file__).resolve().parent.parent / "data" / "dept_data.yaml"
with open(data_path, "r", encoding="utf-8") as f:
    td = yaml.safe_load(f)


def _find_dept(tree, dept_name):
    """在部门树中递归查找指定名称的部门"""
    for d in tree:
        if d["deptName"] == dept_name:
            return d
        children = d.get("children")
        if children:
            found = _find_dept(children, dept_name)
            if found:
                return found
    return None


class TestDeptManager:
    """部门管理 CRUD"""

    def test_list_dept(self, base_api):
        """
        查询部门列表
        验证：返回树形部门 data（非分页）
        """
        resp = base_api.get("/system/dept/list")
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 200
        assert "data" in result
        assert isinstance(result["data"], list)
        assert len(result["data"]) > 0

        logger.info(f"✅ 部门列表：{len(result['data'])}条根节点")

    def test_create_dept(self, base_api, cleanup_ids):
        """
        新增部门 + 自动清理
        验证：创建成功 + 从列表反查 deptId 写入 cleanup_ids 自动删除
        """
        suffix = random_str(8)
        body = {
            "parentId": 100,
            "deptName": f"auto_{suffix}",
            "orderNum": 1
        }

        resp = base_api.post("/system/dept", json=body)
        result = resp.json()

        assert result["code"] == 200

        # 从树形列表反查 deptId（创建响应不返回 deptId）
        list_resp = base_api.get("/system/dept/list")
        tree = list_resp.json()["data"]
        target = _find_dept(tree, body["deptName"])
        if target:
            dept_id = target["deptId"]
            cleanup_ids.append(("dept", dept_id))
            logger.info(f"✅ 创建部门：{body['deptName']} (ID:{dept_id})")

    def test_get_dept_detail(self, base_api):
        """
        查询部门详情
        验证：先取列表第一个部门，再查详情，data 非空且 deptId 匹配
        """
        list_resp = base_api.get("/system/dept/list")
        list_result = list_resp.json()
        assert list_result["code"] == 200
        assert len(list_result["data"]) > 0, "列表为空，无法测试详情"

        first = list_result["data"][0]
        dept_id = first["deptId"]

        resp = base_api.get(f"/system/dept/{dept_id}")
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 200
        assert result["data"] is not None
        assert result["data"]["deptId"] == dept_id

        logger.info(f"✅ 查询部门详情：{result['data']['deptName']} (ID:{dept_id})")

    def test_update_dept(self, base_api, cleanup_ids):
        """
        创建临时部门 → 修改部门名称
        验证：修改后 code == 200
        策略：不修改已有部门，自己创建自己改
        """
        suffix = random_str(8)
        body = {
            "parentId": 100,
            "deptName": f"temp_upd_{suffix}",
            "orderNum": 1
        }
        create_resp = base_api.post("/system/dept", json=body)
        assert create_resp.json()["code"] == 200

        # 从树形列表获取完整部门对象（PUT 需要完整结构）
        list_resp = base_api.get("/system/dept/list")
        tree = list_resp.json()["data"]
        target = _find_dept(tree, body["deptName"])
        assert target is not None, "创建部门后未在列表中查到"

        dept_id = target["deptId"]
        cleanup_ids.append(("dept", dept_id))

        target["deptName"] = f"{body['deptName']}_updated"

        resp = base_api.put("/system/dept", json=target)
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 200

        logger.info(f"✅ 更新部门：{target['deptName']} (ID:{dept_id})")

    def test_delete_dept(self, base_api):
        """
        创建临时部门 -> 删除 -> 验证
        策略：不删已有部门，自己创建自己删
        """
        suffix = random_str(8)
        dept_name = f"temp_del_{suffix}"
        create_resp = base_api.post("/system/dept", json={
            "parentId": 100,
            "deptName": dept_name,
            "orderNum": 1
        })
        assert create_resp.json()["code"] == 200, "创建部门失败，无法测试删除"

        # 从树形列表查询 deptId
        list_resp = base_api.get("/system/dept/list")
        tree = list_resp.json()["data"]
        target = _find_dept(tree, dept_name)
        assert target is not None, "创建后未在列表中查到该部门"

        dept_id = target["deptId"]
        resp = base_api.delete(f"/system/dept/{dept_id}")
        assert resp.status_code == 200

        logger.info(f"✅ 删除部门：{dept_name} (ID:{dept_id})")
