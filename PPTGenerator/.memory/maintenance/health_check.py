#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆系统健康检查脚本

功能：
1. 检查记忆文件是否存在
2. 检查 P0 文件行数，超过阈值提醒归档
3. 检查 P1 文件最后更新时间
4. 生成健康报告
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# 修复 Windows 控制台编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 配置
MEMORY_DIR = Path(__file__).parent.parent
P0_FILE = MEMORY_DIR / "MEMORY_P0.md"
P1_FILE = MEMORY_DIR / "MEMORY_P1.md"
P2_DIR = MEMORY_DIR / "P2"
TELOS_DIR = MEMORY_DIR / "telos"

P0_MAX_LINES = 200  # P0 最大行数
P1_MAX_DAYS = 90    # P1 内容最大天数


def count_lines(filepath):
    """计算文件行数"""
    if not filepath.exists():
        return 0
    with open(filepath, 'r', encoding='utf-8') as f:
        return sum(1 for _ in f)


def get_file_mtime(filepath):
    """获取文件最后修改时间"""
    if not filepath.exists():
        return None
    mtime = os.path.getmtime(filepath)
    return datetime.fromtimestamp(mtime)


def check_p0_health():
    """检查 P0 热记忆健康状态"""
    issues = []

    if not P0_FILE.exists():
        issues.append({
            "level": "ERROR",
            "message": "P0 热记忆文件不存在",
            "file": str(P0_FILE)
        })
        return issues

    lines = count_lines(P0_FILE)
    if lines > P0_MAX_LINES:
        issues.append({
            "level": "WARNING",
            "message": f"P0 文件超过 {P0_MAX_LINES} 行 ({lines} 行)，建议归档部分内容到 P1",
            "file": str(P0_FILE)
        })

    mtime = get_file_mtime(P0_FILE)
    days_since_update = (datetime.now() - mtime).days if mtime else 999
    if days_since_update > 7:
        issues.append({
            "level": "INFO",
            "message": f"P0 已 {days_since_update} 天未更新",
            "file": str(P0_FILE)
        })

    return issues


def check_p1_health():
    """检查 P1 温记忆健康状态"""
    issues = []

    if not P1_FILE.exists():
        issues.append({
            "level": "WARNING",
            "message": "P1 温记忆文件不存在",
            "file": str(P1_FILE)
        })
        return issues

    mtime = get_file_mtime(P1_FILE)
    days_since_update = (datetime.now() - mtime).days if mtime else 999
    if days_since_update > 30:
        issues.append({
            "level": "INFO",
            "message": f"P1 已 {days_since_update} 天未更新，可能有经验未记录",
            "file": str(P1_FILE)
        })

    return issues


def check_telos_health():
    """检查 TELOS 系统健康状态"""
    issues = []

    required_files = [
        "MISSION.md",
        "GOALS.md",
        "PROJECTS.md",
        "LEARNED.md",
        "CHALLENGES.md",
        "IDEAS.md"
    ]

    for filename in required_files:
        filepath = TELOS_DIR / filename
        if not filepath.exists():
            issues.append({
                "level": "WARNING",
                "message": f"TELOS 文件缺失: {filename}",
                "file": str(filepath)
            })

    return issues


def check_p2_health():
    """检查 P2 冷记忆健康状态"""
    issues = []

    if not P2_DIR.exists():
        issues.append({
            "level": "INFO",
            "message": "P2 归档目录不存在，将在需要时创建",
            "file": str(P2_DIR)
        })

    return issues


def generate_report():
    """生成健康检查报告"""
    print("=" * 60)
    print("记忆系统健康检查报告")
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    all_issues = []

    # 检查各部分
    print("\n[1] P0 热记忆")
    p0_issues = check_p0_health()
    all_issues.extend(p0_issues)
    if not p0_issues:
        print("  [OK] 状态良好")
    for issue in p0_issues:
        print(f"  {issue['level']}: {issue['message']}")

    print("\n[2] P1 温记忆")
    p1_issues = check_p1_health()
    all_issues.extend(p1_issues)
    if not p1_issues:
        print("  [OK] 状态良好")
    for issue in p1_issues:
        print(f"  {issue['level']}: {issue['message']}")

    print("\n[3] TELOS 系统")
    telos_issues = check_telos_health()
    all_issues.extend(telos_issues)
    if not telos_issues:
        print("  [OK] 状态良好")
    for issue in telos_issues:
        print(f"  {issue['level']}: {issue['message']}")

    print("\n[4] P2 冷记忆")
    p2_issues = check_p2_health()
    all_issues.extend(p2_issues)
    if not p2_issues:
        print("  [OK] 状态良好")
    for issue in p2_issues:
        print(f"  {issue['level']}: {issue['message']}")

    # 统计
    print("\n" + "=" * 60)
    print("统计信息")
    print("=" * 60)

    error_count = sum(1 for i in all_issues if i['level'] == 'ERROR')
    warning_count = sum(1 for i in all_issues if i['level'] == 'WARNING')
    info_count = sum(1 for i in all_issues if i['level'] == 'INFO')

    print(f"  错误 (ERROR): {error_count}")
    print(f"  警告 (WARNING): {warning_count}")
    print(f"  信息 (INFO): {info_count}")

    # 返回状态码
    if error_count > 0:
        return 1
    elif warning_count > 0:
        return 2
    else:
        return 0


def main():
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(description='记忆系统健康检查')
    parser.add_argument('--json', action='store_true', help='输出 JSON 格式')
    args = parser.parse_args()

    if args.json:
        # JSON 输出模式
        result = {
            "timestamp": datetime.now().isoformat(),
            "p0": {"issues": check_p0_health()},
            "p1": {"issues": check_p1_health()},
            "telos": {"issues": check_telos_health()},
            "p2": {"issues": check_p2_health()}
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 交互式输出
        exit_code = generate_report()
        return exit_code


if __name__ == "__main__":
    exit(main())
