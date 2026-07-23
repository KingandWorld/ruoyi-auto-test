"""
项目入口 —— 一键运行所有测试并生成 Allure 报告

用法：
    python run.py              # 运行所有测试 + 生成报告
    python run.py --no-report  # 只跑测试，不生成报告
    python run.py --open       # 跑测试 + 生成报告 + 自动打开
"""
import sys
import subprocess
from pathlib import Path

REPORT_DIR = Path(__file__).parent / "reports"
HTML_DIR = REPORT_DIR / "html"


def run_tests():
    """执行所有测试用例，输出 Allure JSON 结果"""
    print("=" * 60)
    print("🚀 开始执行接口自动化测试...")
    print("=" * 60)

    cmd = [
        sys.executable, "-m", "pytest", "testcases/",
        "--alluredir", str(REPORT_DIR),
        "--clean-alluredir",
    ]
    result = subprocess.run(cmd)
    return result.returncode == 0


def generate_report():
    """将 Allure JSON 结果编译为 HTML 报告"""
    print("\n📊 生成 Allure 报告...")
    subprocess.run([
        "allure", "generate", str(REPORT_DIR),
        "-o", str(HTML_DIR),
        "--clean",
    ], check=True)
    print(f"✅ 报告已生成：{HTML_DIR / 'index.html'}")


def open_report():
    """打开 Allure 报告"""
    print("\n🌐 打开 Allure 报告...")
    subprocess.run(["allure", "open", str(HTML_DIR)])


if __name__ == "__main__":
    no_report = "--no-report" in sys.argv
    auto_open = "--open" in sys.argv

    success = run_tests()

    if not no_report:
        generate_report()
        if auto_open:
            open_report()

    print("=" * 60)
    print("✅ 测试执行完毕" if success else "❌ 测试存在失败")
    print("=" * 60)
    sys.exit(0 if success else 1)
