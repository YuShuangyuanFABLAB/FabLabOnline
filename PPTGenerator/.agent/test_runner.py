"""
测试运行器 - 用于验证功能是否正确实现
支持三层验证：代码层→目标环境→用户视角
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

# 确保标准输出使用UTF-8编码
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


class TestRunner:
    """测试运行器类"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.feature_list_path = self.project_root / ".agent" / "feature_list.json"
        self.progress_path = self.project_root / ".agent" / "agent-progress.txt"
        self.project_config_path = self.project_root / ".agent" / "templates" / "project_config.json"
        self.features = self._load_features()
        self.project_config = self._load_project_config()

    def _load_features(self) -> dict:
        """加载功能列表"""
        if self.feature_list_path.exists():
            with open(self.feature_list_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"features": []}

    def _load_project_config(self) -> dict:
        """加载项目配置"""
        if self.project_config_path.exists():
            with open(self.project_config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_features(self):
        """保存功能列表"""
        self.features["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        with open(self.feature_list_path, 'w', encoding='utf-8') as f:
            json.dump(self.features, f, ensure_ascii=False, indent=2)

    def get_feature(self, feature_id: str) -> dict:
        """获取指定功能"""
        for feature in self.features.get("features", []):
            if feature["id"] == feature_id:
                return feature
        return None

    def get_next_feature(self) -> dict:
        """获取下一个待开发的功能（最高优先级且依赖已满足）"""
        completed_ids = {f["id"] for f in self.features.get("features", []) if f.get("passes", False)}

        # 按优先级排序
        priority_order = {"high": 0, "medium": 1, "low": 2}

        available_features = []
        for feature in self.features.get("features", []):
            if feature.get("passes", False):
                continue  # 已完成
            # 检查依赖
            blocked_by = feature.get("blocked_by", [])
            if all(dep_id in completed_ids for dep_id in blocked_by):
                available_features.append(feature)

        if not available_features:
            return None

        # 按优先级排序
        available_features.sort(key=lambda x: priority_order.get(x.get("priority", "medium"), 1))
        return available_features[0]

    def run_tests_for_feature(self, feature_id: str) -> bool:
        """运行指定功能的测试"""
        feature = self.get_feature(feature_id)
        if not feature:
            print(f"功能 {feature_id} 不存在")
            return False

        print(f"\n{'='*50}")
        print(f"运行测试: {feature_id} - {feature['description']}")
        print(f"{'='*50}")

        # 检查测试文件是否存在
        test_file = self.project_root / "tests" / f"test_{feature_id.lower()}.py"
        if test_file.exists():
            result = subprocess.run(
                ["python", "-m", "pytest", str(test_file), "-v"],
                cwd=self.project_root
            )
            return result.returncode == 0
        else:
            print(f"测试文件不存在: {test_file}")
            print("尝试运行所有测试...")
            tests_dir = self.project_root / "tests"
            if tests_dir.exists():
                result = subprocess.run(
                    ["python", "-m", "pytest", str(tests_dir), "-v"],
                    cwd=self.project_root
                )
                return result.returncode == 0
            else:
                print("tests目录不存在，跳过自动化测试")
                return self._manual_test_check(feature)

    def _manual_test_check(self, feature: dict) -> bool:
        """手动测试检查清单"""
        print("\n请手动验证以下测试项:")
        print("-" * 40)
        for i, test in enumerate(feature.get("tests", []), 1):
            print(f"  [{i}] {test}")

        print("\n所有测试项是否都通过? (y/n): ", end="")
        response = input().strip().lower()
        return response == 'y'

    def mark_feature_complete(self, feature_id: str):
        """标记功能为完成"""
        for feature in self.features.get("features", []):
            if feature["id"] == feature_id:
                feature["passes"] = True
                self._save_features()
                print(f"✓ 功能 {feature_id} 已标记为完成")
                return True
        return False

    def get_progress_stats(self) -> dict:
        """获取进度统计"""
        total = len(self.features.get("features", []))
        completed = sum(1 for f in self.features.get("features", []) if f.get("passes", False))
        return {
            "total": total,
            "completed": completed,
            "remaining": total - completed,
            "percentage": round(completed / total * 100, 1) if total > 0 else 0
        }

    def print_status(self):
        """打印当前状态"""
        stats = self.get_progress_stats()
        print("\n" + "=" * 50)
        print("项目状态")
        print("=" * 50)
        print(f"总功能数: {stats['total']}")
        print(f"已完成: {stats['completed']}")
        print(f"进行中/待开始: {stats['remaining']}")
        print(f"完成率: {stats['percentage']}%")

        next_feature = self.get_next_feature()
        if next_feature:
            print(f"\n下一个待开发功能:")
            print(f"  ID: {next_feature['id']}")
            print(f"  描述: {next_feature['description']}")
            print(f"  优先级: {next_feature['priority']}")
        else:
            print("\n🎉 所有功能已完成!")

    def update_progress_file(self, session_info: dict):
        """更新进度文件"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        entry = f"""
### [Session] {timestamp}
**状态**: {session_info.get('status', '进行中')}

**完成的功能**:
{chr(10).join(f"- [x] {f}" for f in session_info.get('completed_features', [])) or '- 无'}

**完成的工作**:
{chr(10).join(f"- {w}" for w in session_info.get('work_done', [])) or '- 无'}

**遇到的问题**:
{session_info.get('issues', '无')}

**下一步**:
{session_info.get('next_steps', '继续开发')}
"""

        with open(self.progress_path, 'a', encoding='utf-8') as f:
            f.write(entry)

    def verify_target_environment(self) -> dict:
        """目标环境验证"""
        result = {"success": False, "message": "", "details": []}

        target_env = self.project_config.get("target_environment", {})
        env_type = target_env.get("type", "")

        if env_type == "office":
            return self._verify_office_environment(target_env)
        elif env_type == "web":
            return self._verify_web_environment(target_env)
        else:
            result["message"] = f"未知的目标环境类型: {env_type}"
            return result

    def _verify_office_environment(self, target_env: dict) -> dict:
        """验证Office环境（PPT/Excel等）"""
        result = {"success": False, "message": "", "details": []}

        try:
            import win32com.client
            import pythoncom

            pythoncom.CoInitialize()

            apps = target_env.get("applications", [])
            for app in apps:
                if app == "PowerPoint":
                    ppt = win32com.client.Dispatch("PowerPoint.Application")
                    result["details"].append(f"PowerPoint COM 可用 (版本: {ppt.Version})")
                    # 不退出，保持可用

            result["success"] = True
            result["message"] = "目标环境验证通过"

        except ImportError:
            result["message"] = "缺少pywin32依赖，请运行: pip install pywin32"
        except Exception as e:
            result["message"] = f"目标环境验证失败: {str(e)}"

        return result

    def _verify_web_environment(self, target_env: dict) -> dict:
        """验证Web环境"""
        result = {"success": False, "message": "Web环境验证暂未实现", "details": []}
        return result

    def _get_skill_paths(self) -> list:
        """获取skills目录路径列表（优先全局目录）"""
        paths = []
        # 全局skills目录
        global_skill_path = Path.home() / ".skills"
        if global_skill_path.exists():
            paths.append(global_skill_path)
        # 项目skills目录
        project_skill_path = self.project_root / ".skills"
        if project_skill_path.exists() and project_skill_path not in paths:
            paths.append(project_skill_path)
        return paths

    def lookup_skill(self, keyword: str) -> dict:
        """查找相关skill（支持全局和项目目录）"""
        skill_paths = self._get_skill_paths()

        if not skill_paths:
            return {"found": False, "message": "未找到skills目录（全局或项目）"}

        for skill_path in skill_paths:
            skill_index_path = skill_path / "skill_index.json"

            if not skill_index_path.exists():
                continue

            with open(skill_index_path, 'r', encoding='utf-8') as f:
                skill_index = json.load(f)

            # 在quick_reference中查找
            quick_ref = skill_index.get("quick_reference", {})
            if keyword in quick_ref:
                skill_id = quick_ref[keyword]
                skill_info = skill_index.get("skills", {}).get(skill_id, {})
                skill_file = skill_path / skill_info.get("file", "")
                return {
                    "found": True,
                    "skill_id": skill_id,
                    "skill_file": str(skill_file),
                    "problem": skill_info.get("problem", ""),
                    "solution": skill_info.get("solution", "")
                }

            # 在keywords中搜索
            for skill_id, skill_info in skill_index.get("skills", {}).items():
                if keyword.lower() in [k.lower() for k in skill_info.get("keywords", [])]:
                    skill_file = skill_path / skill_info.get("file", "")
                    return {
                        "found": True,
                        "skill_id": skill_id,
                        "skill_file": str(skill_file),
                        "problem": skill_info.get("problem", ""),
                        "solution": skill_info.get("solution", "")
                    }

        return {"found": False, "message": f"未找到与'{keyword}'相关的skill"}


def main():
    """主函数"""
    runner = TestRunner()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "status":
            runner.print_status()

        elif command == "next":
            next_feature = runner.get_next_feature()
            if next_feature:
                print(f"下一个功能: {next_feature['id']} - {next_feature['description']}")
            else:
                print("所有功能已完成!")

        elif command == "test":
            if len(sys.argv) > 2:
                feature_id = sys.argv[2]
                success = runner.run_tests_for_feature(feature_id)
                sys.exit(0 if success else 1)
            else:
                print("用法: python test_runner.py test <feature_id>")

        elif command == "complete":
            if len(sys.argv) > 2:
                feature_id = sys.argv[2]
                runner.mark_feature_complete(feature_id)
            else:
                print("用法: python test_runner.py complete <feature_id>")

        elif command == "verify":
            """目标环境验证"""
            result = runner.verify_target_environment()
            print("\n" + "=" * 50)
            print("目标环境验证")
            print("=" * 50)
            status = "[OK] 通过" if result['success'] else "[X] 失败"
            print(f"状态: {status}")
            print(f"信息: {result['message']}")
            if result['details']:
                print("\n详情:")
                for detail in result['details']:
                    print(f"  - {detail}")

        elif command == "skill":
            """查找skill"""
            if len(sys.argv) > 2:
                keyword = sys.argv[2]
                result = runner.lookup_skill(keyword)
                print("\n" + "=" * 50)
                print("Skill查找")
                print("=" * 50)
                if result['found']:
                    print(f"Skill ID: {result['skill_id']}")
                    print(f"文件: {result['skill_file']}")
                    print(f"问题: {result['problem']}")
                    print(f"解决方案: {result['solution']}")
                else:
                    print(result.get('message', '未找到'))
            else:
                print("用法: python test_runner.py skill <关键词>")
                print("示例: python test_runner.py skill 颜色")

        elif command == "help":
            print("""
测试运行器命令:

  status              显示项目状态
  next                获取下一个待开发功能
  test <id>           运行指定功能的测试
  complete <id>       标记功能为完成
  verify              验证目标环境（如Office COM）
  skill <关键词>       查找相关skill

示例:
  python test_runner.py status
  python test_runner.py test F001
  python test_runner.py skill 颜色
""")

        else:
            print("未知命令")
            print("可用命令: status, next, test, complete, verify, skill, help")
    else:
        runner.print_status()


if __name__ == "__main__":
    main()
