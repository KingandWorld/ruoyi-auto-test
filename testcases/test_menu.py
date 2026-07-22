"""
菜单管理模块测试
接口路径：GET/POST/PUT/DELETE /system/menu
注意：菜单列表返回 tree 结构（data），不是分页的 rows
"""
import yaml
from pathlib import Path
from common.logger import logger
from common.utils import random_str
from testcases.conftest import cleanup_ids

data_path = Path(__file__).resolve().parent.parent / "data" / "menu_data.yaml"
with open(data_path, "r", encoding="utf-8") as f:
    td = yaml.safe_load(f)


def _find_menu(tree, menu_name):
    """在菜单树中递归查找指定名称的菜单"""
    for m in tree:
        if m["menuName"] == menu_name:
            return m
        children = m.get("children")
        if children:
            found = _find_menu(children, menu_name)
            if found:
                return found
    return None


class TestMenuManager:
    """菜单管理 CRUD"""

    def test_list_menu(self, base_api):
        """
        查询菜单列表
        验证：返回树形菜单 data（非分页）
        """
        resp = base_api.get("/system/menu/list")
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 200
        assert "data" in result
        assert isinstance(result["data"], list)
        assert len(result["data"]) > 0

        logger.info(f"✅ 菜单列表：{len(result['data'])}条根节点")

    def test_create_menu(self, base_api, cleanup_ids):
        """
        新增菜单 + 自动清理
        验证：创建成功 + 从列表反查 menuId 写入 cleanup_ids 自动删除
        """
        suffix = random_str(8)
        body = {
            "parentId": 0,
            "menuType": "M",
            "menuName": f"auto_{suffix}",
            "path": f"/auto_{suffix}",
            "orderNum": 1,
            "status": "0",
            "visible": "0",
            "isFrame": "1"
        }

        resp = base_api.post("/system/menu", json=body)
        result = resp.json()

        assert result["code"] == 200

        # 从树形列表反查 menuId（创建响应不返回 menuId）
        list_resp = base_api.get("/system/menu/list")
        tree = list_resp.json()["data"]
        target = _find_menu(tree, body["menuName"])
        if target:
            menu_id = target["menuId"]
            cleanup_ids.append(("menu", menu_id))
            logger.info(f"✅ 创建菜单：{body['menuName']} (ID:{menu_id})")

    def test_get_menu_detail(self, base_api):
        """
        查询菜单详情
        验证：先取列表第一个菜单，再查详情，data 非空且 menuId 匹配
        """
        list_resp = base_api.get("/system/menu/list")
        list_result = list_resp.json()
        assert list_result["code"] == 200
        assert len(list_result["data"]) > 0, "列表为空，无法测试详情"

        first = list_result["data"][0]
        menu_id = first["menuId"]

        resp = base_api.get(f"/system/menu/{menu_id}")
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 200
        assert result["data"] is not None
        assert result["data"]["menuId"] == menu_id

        logger.info(f"✅ 查询菜单详情：{result['data']['menuName']} (ID:{menu_id})")

    def test_update_menu(self, base_api, cleanup_ids):
        """
        创建临时菜单 → 修改菜单名称
        验证：修改后 code == 200
        策略：不修改已有菜单，自己创建自己改
        """
        suffix = random_str(8)
        body = {
            "parentId": 0,
            "menuType": "M",
            "menuName": f"temp_upd_{suffix}",
            "path": f"/temp_upd_{suffix}",
            "orderNum": 1,
            "status": "0",
            "visible": "0",
            "isFrame": "1"
        }
        create_resp = base_api.post("/system/menu", json=body)
        assert create_resp.json()["code"] == 200

        # 从树形列表获取完整菜单对象（PUT 需要完整结构）
        list_resp = base_api.get("/system/menu/list")
        tree = list_resp.json()["data"]
        target = _find_menu(tree, body["menuName"])
        assert target is not None, "创建菜单后未在列表中查到"

        menu_id = target["menuId"]
        cleanup_ids.append(("menu", menu_id))

        target["menuName"] = f"{body['menuName']}_updated"

        resp = base_api.put("/system/menu", json=target)
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 200

        logger.info(f"✅ 更新菜单：{target['menuName']} (ID:{menu_id})")

    def test_delete_menu(self, base_api):
        """
        创建临时菜单 -> 删除 -> 验证
        策略：不删已有菜单，自己创建自己删
        """
        suffix = random_str(8)
        menu_name = f"temp_del_{suffix}"
        create_resp = base_api.post("/system/menu", json={
            "parentId": 0,
            "menuType": "M",
            "menuName": menu_name,
            "path": f"/temp_del_{suffix}",
            "orderNum": 1,
            "status": "0",
            "visible": "0",
            "isFrame": "1"
        })
        assert create_resp.json()["code"] == 200, "创建菜单失败，无法测试删除"

        # 从树形列表查询 menuId
        list_resp = base_api.get("/system/menu/list")
        tree = list_resp.json()["data"]
        target = _find_menu(tree, menu_name)
        assert target is not None, "创建后未在列表中查到该菜单"

        menu_id = target["menuId"]
        resp = base_api.delete(f"/system/menu/{menu_id}")
        assert resp.status_code == 200

        logger.info(f"✅ 删除菜单：{menu_name} (ID:{menu_id})")
