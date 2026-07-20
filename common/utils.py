"""工具函数：随机数据生成"""
import random
import string
import time
from typing import Literal

CHARSET_ALNUM = string.ascii_lowercase + string.digits
PHONE_PREFIX = ["138", "139", "158", "159", "188", "189"]
EMAIL_DOMAIN = "ruoyi.com"

def random_str(length: int) -> str:
    """生成随机字符串：random_str(6) -> 'a1B2c3'"""
    return ''.join(random.choices(CHARSET_ALNUM, k=length))

def random_phone() -> str:
    """生成随机手机号：random_phone() -> '13812345678'"""
    prefix = random.choice(PHONE_PREFIX)
    suffix = ''.join(random.choices(string.digits, k=8))
    return prefix + suffix

def random_email(prefix: str = "test") -> str:
    """生成随机邮箱：random_email() -> 'test_a1B2c3@ruoyi.com'"""
    return f"{prefix}_{random_str(6)}@{EMAIL_DOMAIN}"

def timestamp_str(
        fmt: Literal["compact", "standard"] = "compact"
) -> str:
    """生成时间戳字符串：timestamp_str() -> '20230706123456'"""
    fmt_map = {
        "compact": "%Y%m%d%H%M%S",
        "standard": "%Y-%m-%d %H:%M:%S"
    }
    return time.strftime(fmt_map[fmt], time.localtime())
