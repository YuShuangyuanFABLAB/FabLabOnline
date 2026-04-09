#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆归档管理脚本

功能：
1. 将 P0 旧内容归档到 P1
2. 将 P1 旧内容归档到 P2
3. 创建按月归档文件
"""

import os
import sys
import re
import shutil
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

P0_MAX_LINES = 200
P1_ARCHIVE_DAYS = 90


def ensure_p2_dir():
    """确保 P2 目录存在"""
    P2_DIR.mkdir(parents=True, exist_ok=True)


def get_current_month_archive():
    """获取当月归档文件路径"""
    ensure_p2_dir()
    month_str = datetime.now().strftime("%Y-%m")
    return P2_DIR / f"archive_{month_str}.md"


def create_monthly_archive_header(filepath):
    """创建月度归档文件头部"""
    if not filepath.exists():
        header = f"""# P2 冷记忆归档 - {datetime.now().strftime("%Y年%m月")}

> 本文件自动生成，记录超过 {P1_ARCHIVE_DAYS} 天的历史内容

---

"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(header)


def archive_from_p0():
    """从 P0 归档内容到 P1"""
    if not P0_FILE.exists():
        print("P0 文件不存在，跳过归档")
        return

    with open(P0_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    if len(lines) <= P0_MAX_LINES:
        print(f"P0 行数 ({len(lines)}) 未超过阈值 ({P0_MAX_LINES})，无需归档")
        return

    print(f"P0 行数 ({len(lines)}) 超过阈值 ({P0_MAX_LINES})，需要归档")

    # TODO: 实现智能归档逻辑
    # 当前版本只提醒，不自动归档
    print("请手动检查 P0 文件，将旧内容移动到 P1")


def archive_from_p1():
    """从 P1 归档内容到 P2"""
    if not P1_FILE.exists():
        print("P1 文件不存在，跳过归档")
        return

    # 检查文件最后修改时间
    mtime = os.path.getmtime(P1_FILE)
    file_age_days = (datetime.now() - datetime.fromtimestamp(mtime)).days

    if file_age_days < P1_ARCHIVE_DAYS:
        print(f"P1 文件年龄 ({file_age_days} 天) 未达到归档阈值 ({P1_ARCHIVE_DAYS} 天)")
        return

    print(f"P1 文件年龄 ({file_age_days} 天) 已达到归档阈值")

    # 创建月度归档
    archive_file = get_current_month_archive()
    create_monthly_archive_header(archive_file)

    # 追加 P1 内容到归档
    with open(P1_FILE, 'r', encoding='utf-8') as f:
        p1_content = f.read()

    archive_entry = f"""
## 归档自 P1 温记忆 ({datetime.now().strftime('%Y-%m-%d')})

{p1_content}

---
"""

    with open(archive_file, 'a', encoding='utf-8') as f:
        f.write(archive_entry)

    print(f"已将 P1 内容归档到 {archive_file}")

    # 清空 P1 文件（保留结构）
    new_p1_content = """# P1 温记忆 (Warm Memory)

> 需要的时候能想起来 - 已完成任务、踩过的坑、学到的教训

---

## 经验教训

(待补充)

---

## 完成的关键功能

(待补充)

---

## 最佳实践

(待补充)

---

*最后更新: {datetime.now().strftime('%Y-%m-%d')}*
"""

    with open(P1_FILE, 'w', encoding='utf-8') as f:
        f.write(new_p1_content)

    print("P1 文件已重置")


def show_status():
    """显示记忆系统状态"""
    print("=" * 60)
    print("记忆归档状态")
    print("=" * 60)

    # P0 状态
    if P0_FILE.exists():
        with open(P0_FILE, 'r', encoding='utf-8') as f:
            lines = len(f.readlines())
        print(f"\nP0 热记忆: {lines} 行 (阈值: {P0_MAX_LINES})")
        if lines > P0_MAX_LINES:
            print("  [!] 需要归档")
        else:
            print("  [OK] 状态良好")
    else:
        print("\nP0 热记忆: 不存在")

    # P1 状态
    if P1_FILE.exists():
        mtime = os.path.getmtime(P1_FILE)
        age = (datetime.now() - datetime.fromtimestamp(mtime)).days
        print(f"\nP1 温记忆: {age} 天前更新 (归档阈值: {P1_ARCHIVE_DAYS} 天)")
        if age > P1_ARCHIVE_DAYS:
            print("  [!] 可以归档")
        else:
            print("  [OK] 状态良好")
    else:
        print("\nP1 温记忆: 不存在")

    # P2 状态
    ensure_p2_dir()
    archives = list(P2_DIR.glob("archive_*.md"))
    print(f"\nP2 冷记忆: {len(archives)} 个归档文件")
    for archive in sorted(archives):
        print(f"  - {archive.name}")


def main():
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(description='记忆归档管理')
    parser.add_argument('command', choices=['status', 'archive', 'auto'],
                        help='status: 显示状态, archive: 执行归档, auto: 自动检查并归档')
    args = parser.parse_args()

    if args.command == 'status':
        show_status()
    elif args.command == 'archive':
        print("执行归档...")
        archive_from_p0()
        archive_from_p1()
    elif args.command == 'auto':
        # 自动模式：只在实际需要时归档
        print("自动归档检查...")
        archive_from_p0()
        archive_from_p1()


if __name__ == "__main__":
    main()
