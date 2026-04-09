# -*- coding: utf-8 -*-
"""
配置管理器
负责管理应用程序的配置文件
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional


def get_app_dir() -> Path:
    """
    获取应用程序所在目录（用于写入配置等）
    兼容开发和打包环境
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后 - exe 所在目录
        return Path(sys.executable).parent
    else:
        # 开发环境 - 项目根目录
        return Path(__file__).parent.parent.parent


class ConfigManager:
    """配置管理器类"""

    DEFAULT_SETTINGS = {
        # 窗口设置
        "window_geometry": "",
        "window_state": "",
        "splitter_state": "",

        # 默认值
        "default_teacher": "",
        "default_class_hours": 2,

        # 课程系列配置
        "course_series": [
            {"name": "机械臂设计", "level": 1},
            {"name": "玩具大改造", "level": 1}
        ],
        "current_series_index": 0,

        # 班级管理
        "classes": [],
        "current_class_id": "",
        "students_by_class": {},

        # 最近使用的数据
        "recent_students": [],
        "recent_teachers": [],
        "recent_courses": [],

        # 布局配置
        "layout_config": {
            "include_course_info": True,
            "include_model_display": True,
            "model_display_count": 1,
            "include_double_image": False,
            "include_program_display": False,
            "include_vehicle_display": False,
            "include_work_display": True
        },

        # 模板路径
        "template_path": "templates/课程反馈.pptx",
        "output_path": "output",

        # 其他设置
        "auto_save": True,
        "show_preview": True,

        # 学员评价持久化
        "student_last_evaluation": {},  # {class_id: {student_name: {评价数据}}}
        "default_other_notes": "",      # 默认注意事项

        # 学员独立课时编号
        "student_next_lesson": {},      # {class_id: {student_name: 课时编号}}

        # 主题设置
        "theme": "light"                # "light" | "dark"
    }

    def __init__(self, config_dir: str = None):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目录，默认为应用程序目录下的config文件夹
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # 使用应用程序目录（兼容开发和打包环境）
            self.config_dir = get_app_dir() / "config"

        self.settings_file = self.config_dir / "settings.json"
        self.colors_file = self.config_dir / "colors.json"

        # 确保目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # 加载配置
        self._settings: Dict[str, Any] = {}
        self._colors: Dict[str, str] = {}
        self._load_settings()
        self._load_colors()

    @property
    def settings(self) -> Dict[str, Any]:
        """获取设置"""
        return self._settings

    @property
    def colors(self) -> Dict[str, str]:
        """获取颜色配置"""
        return self._colors

    def _load_settings(self):
        """加载设置"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self._settings = json.load(f)
                # 合并默认值（处理新增的设置项）
                for key, value in self.DEFAULT_SETTINGS.items():
                    if key not in self._settings:
                        self._settings[key] = value
            except Exception as e:
                print(f"加载设置失败: {e}")
                self._settings = self.DEFAULT_SETTINGS.copy()
        else:
            self._settings = self.DEFAULT_SETTINGS.copy()
            self.save_settings()

    def _load_colors(self):
        """加载颜色配置"""
        default_colors = {
            "highlight": "#0070C0",  # 重点（蓝色）
            "difficulty": "#ED7D31",  # 难点（橙色）
            "excellent": "#00B050",   # 优秀（绿色）
            "good": "#0070C0",        # 良好（蓝色）
            "medium": "#FFC000",      # 中等（黄色）
            "poor": "#FF0000",        # 较差（红色）
        }

        if self.colors_file.exists():
            try:
                with open(self.colors_file, 'r', encoding='utf-8') as f:
                    self._colors = json.load(f)
                # 合并默认值
                for key, value in default_colors.items():
                    if key not in self._colors:
                        self._colors[key] = value
            except Exception as e:
                print(f"加载颜色配置失败: {e}")
                self._colors = default_colors.copy()
        else:
            self._colors = default_colors.copy()
            self.save_colors()

    def save_settings(self):
        """保存设置"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存设置失败: {e}")

    def save_colors(self):
        """保存颜色配置"""
        try:
            with open(self.colors_file, 'w', encoding='utf-8') as f:
                json.dump(self._colors, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存颜色配置失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取设置值

        Args:
            key: 设置键名
            default: 默认值

        Returns:
            设置值
        """
        return self._settings.get(key, default)

    def set(self, key: str, value: Any):
        """
        设置值

        Args:
            key: 设置键名
            value: 设置值
        """
        self._settings[key] = value

    def get_color(self, name: str) -> str:
        """
        获取颜色值

        Args:
            name: 颜色名称

        Returns:
            颜色值（十六进制）
        """
        return self._colors.get(name, "#000000")

    def reset_to_defaults(self):
        """重置为默认设置"""
        self._settings = self.DEFAULT_SETTINGS.copy()
        self.save_settings()

    # ==================== 最近使用的数据管理 ====================

    def add_recent_student(self, name: str, max_count: int = 20):
        """添加最近使用的学生"""
        recent = self._settings.get("recent_students", [])
        if name in recent:
            recent.remove(name)
        recent.insert(0, name)
        self._settings["recent_students"] = recent[:max_count]
        self.save_settings()

    def add_recent_teacher(self, name: str, max_count: int = 20):
        """添加最近使用的教师"""
        recent = self._settings.get("recent_teachers", [])
        if name in recent:
            recent.remove(name)
        recent.insert(0, name)
        self._settings["recent_teachers"] = recent[:max_count]
        self.save_settings()

    def add_recent_course(self, content: str, max_count: int = 20):
        """添加最近使用的课程内容"""
        recent = self._settings.get("recent_courses", [])
        if content in recent:
            recent.remove(content)
        recent.insert(0, content)
        self._settings["recent_courses"] = recent[:max_count]
        self.save_settings()

    def get_recent_students(self) -> List[str]:
        """获取最近使用的学生列表"""
        return self._settings.get("recent_students", [])

    def get_recent_teachers(self) -> List[str]:
        """获取最近使用的教师列表"""
        return self._settings.get("recent_teachers", [])

    def get_recent_courses(self) -> List[str]:
        """获取最近使用的课程内容列表"""
        return self._settings.get("recent_courses", [])

    # ==================== 布局配置管理 ====================

    def get_layout_config(self) -> Dict[str, Any]:
        """获取布局配置"""
        return self._settings.get("layout_config", self.DEFAULT_SETTINGS["layout_config"])

    def set_layout_config(self, config: Dict[str, Any]):
        """设置布局配置"""
        self._settings["layout_config"] = config
        self.save_settings()

    # ==================== 路径管理 ====================

    def get_template_path(self) -> str:
        """获取模板路径"""
        return self._settings.get("template_path", "templates/课程反馈.pptx")

    def set_template_path(self, path: str):
        """设置模板路径"""
        self._settings["template_path"] = path
        self.save_settings()

    def get_output_path(self) -> str:
        """获取输出路径"""
        return self._settings.get("output_path", "output")

    def set_output_path(self, path: str):
        """设置输出路径"""
        self._settings["output_path"] = path
        self.save_settings()

    def get_class_output_path(self, class_id: str) -> str:
        """
        获取指定班级的输出路径，如果没有则返回默认路径

        Args:
            class_id: 班级ID

        Returns:
            班级输出路径，如果无效则返回默认输出路径
        """
        class_paths = self._settings.get("class_output_paths", {})
        path = class_paths.get(class_id, "")
        # 检查路径是否有效
        if path and os.path.isdir(path):
            return path
        return self.get_output_path()  # 返回默认路径

    def set_class_output_path(self, class_id: str, path: str):
        """
        设置指定班级的输出路径

        Args:
            class_id: 班级ID
            path: 输出路径
        """
        if "class_output_paths" not in self._settings:
            self._settings["class_output_paths"] = {}
        self._settings["class_output_paths"][class_id] = path
        self.save_settings()

    # ==================== 课程系列管理 ====================

    def get_course_series(self) -> List[Dict[str, Any]]:
        """获取课程系列列表"""
        return self._settings.get("course_series", [])

    def add_course_series(self, name: str, level: int) -> bool:
        """
        添加新的课程系列

        Args:
            name: 系列名称
            level: 阶数

        Returns:
            是否添加成功（如果已存在则返回False）
        """
        series_list = self._settings.get("course_series", [])

        # 检查是否已存在相同名称和阶数的系列
        for s in series_list:
            if s.get("name") == name and s.get("level") == level:
                return False

        series_list.append({"name": name, "level": level})
        self._settings["course_series"] = series_list
        self.save_settings()
        return True

    def remove_course_series(self, index: int) -> bool:
        """
        删除课程系列

        Args:
            index: 系列索引

        Returns:
            是否删除成功
        """
        series_list = self._settings.get("course_series", [])
        if 0 <= index < len(series_list):
            series_list.pop(index)
            self._settings["course_series"] = series_list

            # 调整当前选择索引
            current_index = self._settings.get("current_series_index", 0)
            if current_index >= len(series_list):
                self._settings["current_series_index"] = max(0, len(series_list) - 1)
            elif current_index > index:
                self._settings["current_series_index"] = current_index - 1

            self.save_settings()
            return True
        return False

    def get_current_series(self) -> Dict[str, Any]:
        """获取当前选择的系列"""
        series_list = self._settings.get("course_series", [])
        index = self._settings.get("current_series_index", 0)

        if series_list and 0 <= index < len(series_list):
            return series_list[index]
        elif series_list:
            return series_list[0]
        else:
            return {"name": "机械臂设计", "level": 1}  # 默认值

    def set_current_series(self, index: int):
        """设置当前选择的系列"""
        series_list = self._settings.get("course_series", [])
        if 0 <= index < len(series_list):
            self._settings["current_series_index"] = index
            self.save_settings()

    # ==================== 班级管理 ====================

    def get_classes(self) -> List[Dict[str, Any]]:
        """获取班级列表"""
        return self._settings.get("classes", [])

    def add_class(self, name: str, teacher: str = "") -> str:
        """
        添加新班级

        Args:
            name: 班级名称（如"星期一 14:00"）
            teacher: 默认授课老师

        Returns:
            班级ID
        """
        import uuid
        class_id = f"cls_{uuid.uuid4().hex[:8]}"
        classes = self._settings.get("classes", [])

        # 检查是否已存在同名班级
        for c in classes:
            if c.get("name") == name:
                return ""  # 已存在

        classes.append({"id": class_id, "name": name, "teacher": teacher, "series_index": 0})
        self._settings["classes"] = classes
        self.save_settings()
        return class_id

    def remove_class(self, class_id: str) -> bool:
        """
        删除班级

        Args:
            class_id: 班级ID

        Returns:
            是否删除成功
        """
        classes = self._settings.get("classes", [])
        for i, c in enumerate(classes):
            if c.get("id") == class_id:
                classes.pop(i)
                self._settings["classes"] = classes

                # 如果删除的是当前班级，清空选择
                if self._settings.get("current_class_id") == class_id:
                    self._settings["current_class_id"] = ""

                # 删除关联的学员数据
                students_by_class = self._settings.get("students_by_class", {})
                if class_id in students_by_class:
                    del students_by_class[class_id]
                    self._settings["students_by_class"] = students_by_class

                self.save_settings()
                return True
        return False

    def get_current_class(self) -> Dict[str, Any]:
        """获取当前选择的班级"""
        classes = self._settings.get("classes", [])
        current_id = self._settings.get("current_class_id", "")

        for c in classes:
            if c.get("id") == current_id:
                return c

        return {}

    def set_current_class(self, class_id: str):
        """设置当前选择的班级"""
        self._settings["current_class_id"] = class_id
        self.save_settings()

    def update_class_teacher(self, class_id: str, teacher: str) -> bool:
        """
        更新班级的默认老师

        Args:
            class_id: 班级ID
            teacher: 老师姓名

        Returns:
            是否更新成功
        """
        classes = self._settings.get("classes", [])
        for c in classes:
            if c.get("id") == class_id:
                c["teacher"] = teacher
                self._settings["classes"] = classes
                self.save_settings()
                return True
        return False

    def get_class_series_index(self, class_id: str) -> int:
        """
        获取班级关联的课程系列索引

        Args:
            class_id: 班级ID

        Returns:
            课程系列索引（默认为0）
        """
        classes = self._settings.get("classes", [])
        for c in classes:
            if c.get("id") == class_id:
                return c.get("series_index", 0)
        return 0

    def set_class_series_index(self, class_id: str, series_index: int) -> bool:
        """
        设置班级关联的课程系列索引

        Args:
            class_id: 班级ID
            series_index: 课程系列索引

        Returns:
            是否设置成功
        """
        classes = self._settings.get("classes", [])
        for c in classes:
            if c.get("id") == class_id:
                c["series_index"] = series_index
                self._settings["classes"] = classes
                self.save_settings()
                return True
        return False

    def get_class_layout_config(self, class_id: str) -> Optional[Dict[str, Any]]:
        """
        获取班级的母版配置

        Args:
            class_id: 班级ID

        Returns:
            母版配置字典，如果班级没有自定义配置则返回None
        """
        classes = self._settings.get("classes", [])
        for c in classes:
            if c.get("id") == class_id:
                return c.get("layout_config")
        return None

    def set_class_layout_config(self, class_id: str, config: Dict[str, Any]) -> bool:
        """
        设置班级的母版配置

        Args:
            class_id: 班级ID
            config: 母版配置字典

        Returns:
            是否设置成功
        """
        classes = self._settings.get("classes", [])
        for c in classes:
            if c.get("id") == class_id:
                c["layout_config"] = config
                self._settings["classes"] = classes
                self.save_settings()
                return True
        return False

    # ==================== 学员管理 ====================

    def get_students_by_class(self, class_id: str) -> List[Dict[str, str]]:
        """
        获取班级学员列表

        Args:
            class_id: 班级ID

        Returns:
            学员列表 [{"name": "张三", "nickname": "小明"}, ...]
        """
        students_by_class = self._settings.get("students_by_class", {})
        return students_by_class.get(class_id, [])

    def add_student(self, class_id: str, name: str, nickname: str = "") -> bool:
        """
        添加学员

        Args:
            class_id: 班级ID
            name: 学员姓名
            nickname: 学员昵称（可选）

        Returns:
            是否添加成功
        """
        if not class_id or not name:
            return False

        students_by_class = self._settings.get("students_by_class", {})
        if class_id not in students_by_class:
            students_by_class[class_id] = []

        # 检查是否已存在同名学员
        for s in students_by_class[class_id]:
            if s.get("name") == name:
                return False

        students_by_class[class_id].append({"name": name, "nickname": nickname})
        self._settings["students_by_class"] = students_by_class
        self.save_settings()
        return True

    def remove_student(self, class_id: str, index: int) -> bool:
        """
        删除学员

        Args:
            class_id: 班级ID
            index: 学员索引

        Returns:
            是否删除成功
        """
        students_by_class = self._settings.get("students_by_class", {})
        if class_id in students_by_class:
            students = students_by_class[class_id]
            if 0 <= index < len(students):
                students.pop(index)
                self._settings["students_by_class"] = students_by_class
                self.save_settings()
                return True
        return False

    def update_student(self, class_id: str, index: int, name: str, nickname: str = "") -> bool:
        """
        更新学员信息

        Args:
            class_id: 班级ID
            index: 学员索引
            name: 学员姓名
            nickname: 学员昵称

        Returns:
            是否更新成功
        """
        students_by_class = self._settings.get("students_by_class", {})
        if class_id in students_by_class:
            students = students_by_class[class_id]
            if 0 <= index < len(students):
                students[index] = {"name": name, "nickname": nickname}
                self._settings["students_by_class"] = students_by_class
                self.save_settings()
                return True
        return False

    # ==================== 学员评价持久化 ====================

    def get_student_last_evaluation(self, class_id: str, student_name: str) -> Dict[str, str]:
        """
        获取学员上次评价数据

        Args:
            class_id: 班级ID
            student_name: 学员姓名

        Returns:
            评价数据字典，如果不存在返回空字典
        """
        student_eval = self._settings.get("student_last_evaluation", {})
        class_eval = student_eval.get(class_id, {})
        return class_eval.get(student_name, {})

    def save_student_last_evaluation(self, class_id: str, student_name: str, eval_data: Dict[str, str]):
        """
        保存学员评价数据（只保存独立字段）

        Args:
            class_id: 班级ID
            student_name: 学员姓名
            eval_data: 评价数据字典
        """
        if "student_last_evaluation" not in self._settings:
            self._settings["student_last_evaluation"] = {}

        if class_id not in self._settings["student_last_evaluation"]:
            self._settings["student_last_evaluation"][class_id] = {}

        # 只保存独立字段（排除共享字段）
        independent_fields = [
            'logic_thinking', 'content_understanding', 'task_completion',
            'listening_habit', 'problem_solving', 'independent_analysis',
            'knowledge_proficiency', 'imagination_creativity', 'frustration_handling',
            'learning_method', 'hands_on_ability', 'focus_efficiency',
            'overall_evaluation', 'last_homework_status', 'additional_comments'
        ]

        filtered_data = {k: v for k, v in eval_data.items() if k in independent_fields}
        self._settings["student_last_evaluation"][class_id][student_name] = filtered_data
        self.save_settings()

    def get_default_other_notes(self) -> str:
        """获取默认注意事项"""
        return self._settings.get("default_other_notes", "")

    def save_default_other_notes(self, notes: str):
        """保存默认注意事项"""
        self._settings["default_other_notes"] = notes
        self.save_settings()

    # ==================== 课时编号管理 ====================

    def get_next_lesson_number(self, class_id: str) -> int:
        """
        获取班级的下次课时编号

        Args:
            class_id: 班级ID

        Returns:
            下次课时编号（默认为1）
        """
        classes = self._settings.get("classes", [])
        for c in classes:
            if c.get("id") == class_id:
                return c.get("next_lesson_number", 1)
        return 1

    def set_next_lesson_number(self, class_id: str, lesson_number: int):
        """
        设置班级的下次课时编号

        Args:
            class_id: 班级ID
            lesson_number: 下次课时编号
        """
        classes = self._settings.get("classes", [])
        for c in classes:
            if c.get("id") == class_id:
                c["next_lesson_number"] = lesson_number
                self._settings["classes"] = classes
                self.save_settings()
                return

    def record_lesson_generated(self, class_id: str, lesson_number: int):
        """
        记录班级已生成某课时的PPT，并设置下次课时编号

        Args:
            class_id: 班级ID
            lesson_number: 当前生成的课时编号
        """
        # 下次 = 当前 + 1
        self.set_next_lesson_number(class_id, lesson_number + 1)

    # ==================== 学员独立课时编号管理 ====================

    def get_student_next_lesson_number(self, class_id: str, student_name: str) -> int:
        """
        获取学员的下次课时编号（学员独立）

        Args:
            class_id: 班级ID
            student_name: 学员姓名

        Returns:
            学员的下次课时编号（默认为1）
        """
        student_lessons = self._settings.get("student_next_lesson", {})
        if class_id in student_lessons:
            return student_lessons[class_id].get(student_name, 1)
        return 1

    def set_student_next_lesson_number(self, class_id: str, student_name: str, lesson_number: int):
        """
        设置学员的下次课时编号（学员独立）

        Args:
            class_id: 班级ID
            student_name: 学员姓名
            lesson_number: 下次课时编号
        """
        if "student_next_lesson" not in self._settings:
            self._settings["student_next_lesson"] = {}

        if class_id not in self._settings["student_next_lesson"]:
            self._settings["student_next_lesson"][class_id] = {}

        self._settings["student_next_lesson"][class_id][student_name] = lesson_number
        self.save_settings()

    # ==================== 主题管理 ====================

    def get_theme(self) -> str:
        """
        获取当前主题

        Returns:
            主题名称: "light" 或 "dark"
        """
        return self._settings.get("theme", "light")

    def set_theme(self, theme: str):
        """
        设置主题

        Args:
            theme: 主题名称 "light" 或 "dark"
        """
        self._settings["theme"] = theme
        self.save_settings()

    # ==================== 配置导出/导入 ====================

    # 导出时排除的机器相关字段
    _EXPORT_EXCLUDE_KEYS = {
        "window_geometry", "window_state", "splitter_state",
    }

    def export_config(self, file_path: str) -> bool:
        """
        导出配置到文件（排除机器相关的窗口状态）

        Args:
            file_path: 导出文件路径

        Returns:
            是否导出成功
        """
        try:
            from datetime import datetime

            export_data = {
                "_version": "1.0",
                "_export_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "_app": "PPTGenerator",
            }

            # 导出设置（排除窗口状态等机器相关字段）
            export_data["settings"] = {
                k: v for k, v in self._settings.items()
                if k not in self._EXPORT_EXCLUDE_KEYS
            }

            # 导出颜色配置
            export_data["colors"] = dict(self._colors)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False

    def import_config(self, file_path: str) -> bool:
        """
        从文件导入配置（合并到当前配置）

        Args:
            file_path: 导入文件路径

        Returns:
            是否导入成功
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            # 验证文件格式
            if import_data.get("_app") != "PPTGenerator":
                print("导入失败: 不是有效的 PPTGenerator 配置文件")
                return False

            imported_settings = import_data.get("settings", {})
            imported_colors = import_data.get("colors", {})

            if not imported_settings and not imported_colors:
                print("导入失败: 配置文件为空")
                return False

            # 合并设置（保留窗口状态等当前机器的状态）
            for key, value in imported_settings.items():
                self._settings[key] = value

            # 合并颜色
            if imported_colors:
                for key, value in imported_colors.items():
                    self._colors[key] = value

            self.save_settings()
            self.save_colors()
            return True
        except json.JSONDecodeError:
            print("导入失败: 文件格式错误")
            return False
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False

    # ==================== 选择性导出/导入 ====================

    def read_config_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        读取并验证配置文件（不合并），供导入对话框预览用

        Args:
            file_path: 配置文件路径

        Returns:
            解析后的配置字典，失败返回 None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data.get("_app") != "PPTGenerator":
                return None
            return data
        except Exception:
            return None

    def export_config_selective(self, file_path: str, selection: Dict[str, Any]) -> bool:
        """
        选择性导出配置

        Args:
            file_path: 导出文件路径
            selection: {
                "selected_class_ids": [str],
                "include_course_series": bool,
                "include_colors": bool,
                "include_recent": bool,
                "include_defaults": bool,
            }

        Returns:
            是否导出成功
        """
        try:
            from datetime import datetime

            export_data = {
                "_version": "1.0",
                "_export_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "_app": "PPTGenerator",
            }

            settings = {}
            selected_ids = set(selection.get("selected_class_ids", []))

            # 导出选中的班级及其关联数据
            classes = self._settings.get("classes", [])
            students_by_class = self._settings.get("students_by_class", {})
            student_eval = self._settings.get("student_last_evaluation", {})
            student_lesson = self._settings.get("student_next_lesson", {})
            class_output_paths = self._settings.get("class_output_paths", {})

            settings["classes"] = [c for c in classes if c.get("id") in selected_ids]
            settings["students_by_class"] = {
                k: v for k, v in students_by_class.items() if k in selected_ids
            }
            settings["student_last_evaluation"] = {
                k: v for k, v in student_eval.items() if k in selected_ids
            }
            settings["student_next_lesson"] = {
                k: v for k, v in student_lesson.items() if k in selected_ids
            }
            if any(k in class_output_paths for k in selected_ids):
                settings["class_output_paths"] = {
                    k: v for k, v in class_output_paths.items() if k in selected_ids
                }

            # 可选：课程系列
            if selection.get("include_course_series"):
                settings["course_series"] = self._settings.get("course_series", [])
                settings["current_series_index"] = self._settings.get("current_series_index", 0)

            # 可选：最近使用记录
            if selection.get("include_recent"):
                for key in ("recent_students", "recent_teachers", "recent_courses"):
                    if key in self._settings:
                        settings[key] = self._settings[key]

            # 可选：默认值
            if selection.get("include_defaults"):
                for key in ("default_teacher", "default_class_hours",
                            "default_other_notes", "theme"):
                    if key in self._settings:
                        settings[key] = self._settings[key]

            export_data["settings"] = settings

            # 可选：颜色配置
            if selection.get("include_colors"):
                export_data["colors"] = dict(self._colors)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"选择性导出失败: {e}")
            return False

    def import_config_selective(self, file_path: str, selection: Dict[str, Any]) -> bool:
        """
        选择性导入配置

        Args:
            file_path: 导入文件路径
            selection: {
                "selected_class_ids": [str],
                "conflict_resolutions": {class_id: "copy"/"skip"},
                "include_course_series": bool,
                "include_colors": bool,
                "include_recent": bool,
                "include_defaults": bool,
            }

        Returns:
            是否导入成功
        """
        try:
            import uuid

            import_data = self.read_config_file(file_path)
            if not import_data:
                return False

            imported_settings = import_data.get("settings", {})
            imported_colors = import_data.get("colors", {})
            conflict_resolutions = selection.get("conflict_resolutions", {})

            # 获取当前班级名称集合（用于冲突检测）
            existing_class_names = {
                c.get("name") for c in self._settings.get("classes", [])
            }

            # 导入选中的班级
            selected_ids = set(selection.get("selected_class_ids", []))
            imported_classes = imported_settings.get("classes", [])
            imported_students = imported_settings.get("students_by_class", {})
            imported_eval = imported_settings.get("student_last_evaluation", {})
            imported_lesson = imported_settings.get("student_next_lesson", {})
            imported_paths = imported_settings.get("class_output_paths", {})

            for cls in imported_classes:
                class_id = cls.get("id", "")
                if class_id not in selected_ids:
                    continue

                resolution = conflict_resolutions.get(class_id, "copy")
                class_name = cls.get("name", "")

                # 检查冲突
                if class_name in existing_class_names:
                    if resolution == "skip":
                        continue
                    # 创建副本：生成新 ID
                    new_id = f"cls_{uuid.uuid4().hex[:8]}"
                    cls = dict(cls, id=new_id)
                    class_id = new_id

                # 添加班级
                self._settings.setdefault("classes", []).append(cls)
                existing_class_names.add(class_name)

                # 合并学员（同名跳过）
                if class_id in imported_students:
                    current_students = self._settings.get("students_by_class", {}).get(class_id, [])
                    current_names = {s.get("name") for s in current_students}
                    new_students = list(current_students)
                    for s in imported_students[class_id]:
                        if s.get("name") not in current_names:
                            new_students.append(s)
                    self._settings.setdefault("students_by_class", {})[class_id] = new_students

                # 合并评价（覆盖）
                if class_id in imported_eval:
                    self._settings.setdefault("student_last_evaluation", {})[class_id] = imported_eval[class_id]

                # 合并课时编号（取较大值）
                if class_id in imported_lesson:
                    current_lessons = self._settings.get("student_next_lesson", {}).get(class_id, {})
                    merged = dict(current_lessons)
                    for name, num in imported_lesson[class_id].items():
                        merged[name] = max(merged.get(name, 0), num)
                    self._settings.setdefault("student_next_lesson", {})[class_id] = merged

                # 合并输出路径
                if class_id in imported_paths:
                    self._settings.setdefault("class_output_paths", {})[class_id] = imported_paths[class_id]

            # 可选：课程系列
            if selection.get("include_course_series"):
                for series in imported_settings.get("course_series", []):
                    self.add_course_series(
                        series.get("name", ""), series.get("level", 1)
                    )

            # 可选：颜色
            if selection.get("include_colors") and imported_colors:
                for key, value in imported_colors.items():
                    self._colors[key] = value
                self.save_colors()

            # 可选：最近记录（合并去重）
            if selection.get("include_recent"):
                for key in ("recent_students", "recent_teachers", "recent_courses"):
                    current = self._settings.get(key, [])
                    imported = imported_settings.get(key, [])
                    merged = list(current)
                    for item in imported:
                        if item not in merged:
                            merged.append(item)
                    self._settings[key] = merged[:20]

            # 可选：默认值（仅覆盖非空值）
            if selection.get("include_defaults"):
                for key in ("default_teacher", "default_other_notes"):
                    val = imported_settings.get(key, "")
                    if val:
                        self._settings[key] = val
                for key in ("default_class_hours",):
                    val = imported_settings.get(key)
                    if val is not None:
                        self._settings[key] = val
                if "theme" in imported_settings:
                    self._settings["theme"] = imported_settings["theme"]

            self.save_settings()
            return True
        except Exception as e:
            print(f"选择性导入失败: {e}")
            return False
