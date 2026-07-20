"""
BaseApi 基类 —— RuoYi 接口自动化测试框架（RuoYi-Vue JWT 版）

设计思路：
  1. 使用 requests.Session 保持会话，自动管理 cookie
  2. RuoYi-Vue 使用 JWT Token 鉴权，每次请求自动注入 Authorization 头
  3. 登录使用 JSON 提交（@RequestBody），与 Shiro 版不同
  4. 统一的异常处理：Timeout / ConnectionError
  5. 每个请求前后打印日志，方便排查问题
"""
import json

import requests
import yaml
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

config_path = Path(__file__).resolve().parent.parent / "config" / "config.yaml"
with open(config_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)


class BaseApi:
    """接口请求基类"""

    def __init__(self):
        self.base_url = config["base"]["base_url"]
        self.timeout = config["base"]["timeout"]

        self.session = requests.Session()
        self.session.headers.update(config["base"]["headers"])

        self.token = None

    #   ==========  统一请求入口  ==========

    def request(self, method, url, **kwargs):
        """统一请求入口，自动添加 base_url 和 token"""
        full_url = self.base_url + url

        # 自动注入 token
        if self.token:
            kwargs.setdefault("headers", {})
            kwargs["headers"]["Authorization"] = f"Bearer {self.token}"

        # 设置超时
        kwargs.setdefault("timeout", self.timeout)

        # 日志：请求详情
        logger.info(f"▶ {method} {full_url}")
        if kwargs.get("json"):
            logger.info(f"  Body: {json.dumps(kwargs['json'], ensure_ascii=False)}")

        # 发送请求 + 异常处理
        try:
            response = self.session.request(method, full_url, **kwargs)
            logger.info(f"◀ {response.status_code} | 耗时：{response.elapsed.total_seconds()} 秒")
            return response
        except requests.exceptions.Timeout:
            logger.error(f"⏰ 请求超时：{full_url}")
            raise
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 连接错误，请确认 RuoYi 服务已启动：{full_url}")
            raise

    #   ==========  便捷方法  ==========

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)

    def put(self, url, **kwargs):
        return self.request("PUT", url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request("DELETE", url, **kwargs)

    #   ==========  登录方法（RuoYi-Vue JWT 版）  ==========

    def login(self, username=None, password=None):
        """登录方法（RuoYi-Vue JWT 版）

        - 使用 JSON 提交（controller 为 @RequestBody，与 Shiro 版不同）
        - 成功后提取 JWT token 存入 self.token，后续请求自动注入
        """
        if username is None:
            username = config["base"]["admin"]["username"]
            password = config["base"]["admin"]["password"]

        login_data = {"username": username, "password": password}
        logger.info(f"[登录] 尝试登录：{username}")

        response = self.post("/login", json=login_data)  # json= 发 JSON

        if response.status_code == 200:
            result = response.json()
            code = result.get("code")
            if code == 200:
                token = result.get("token")
                if token:
                    self.token = token
                    logger.info(f"[登录成功] Token: {token[:30]}...")
                    return token

            logger.error(f"[登录失败] 业务错误({code})：{result.get('msg')}")
            return None

        logger.error(f"[登录失败] HTTP 状态码：{response.status_code}")
        return None
