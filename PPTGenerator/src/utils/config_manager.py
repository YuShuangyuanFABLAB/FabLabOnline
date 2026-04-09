# -*- coding: utf-8 -*-
"""
配置管理器
负责读取和保存配置文件
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """配置管理器类"""

    DEFAULT_CONFIG = {
        "version": "1.0",
        "layout_selection": {
            "include_course_info": True,
            "include_model_display": True,
            "model_display_count": 1,
            "include_double_image": False,
            "include_program_display": False,
            "include_vehicle_display": False,
            "include_work_display": True
        },
        "common_data": {
            "students": [],
            "teachers": [],
            "courses": [],
            "default_class_hours": 2
        },
        "paths": {
            "last_save_path": "",
            "last_excel_path": "",
            "template_path": ""
        },
        "window": {
            "width": 1200,
            "height": 800,
            "x": 100,
            "y": 100
        }
    }

    def __init__(self, config_path: str = "config/settings.json"):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._load()

    def _load(self):
        """加载配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                self.config = self.DEFAULT_CONFIG.copy()
        else:
            self.config = self.DEFAULT_CONFIG.copy()
            self._save()

    def _save(self):
        """保存配置文件"""
        # 确保目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键（支持点号分隔的嵌套键）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any, save: bool = True):
        """
        设置配置值

        Args:
            key: 配置键（支持点号分隔的嵌套键）
            value: 配置值
            save: 是否立即保存
        """
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

        if save:
            self._save()

    def add_to_list(self, key: str, item: str, max_items: int = 10):
        """
        添加项目到列表（用于常用数据）

        Args:
            key: 配置键
            item: 要添加的项目
            max_items: 最大保留数量
        """
        lst = self.get(key, [])
        if item in lst:
            lst.remove(item)
        lst.insert(0, item)
        lst = lst[:max_items]
        self.set(key, lst)

    def get_layout_config(self) -> Dict[str, Any]:
        """获取布局配置"""
        return self.get("layout_selection", {})

    def set_layout_config(self, config: Dict[str, Any]):
        """设置布局配置"""
        self.set("layout_selection", config)

    def get_common_students(self) -> list:
        """获取常用学生列表"""
        return self.get("common_data.students", [])

    def add_common_student(self, name: str):
        """添加常用学生"""
        self.add_to_list("common_data.students", name)

    def get_common_teachers(self) -> list:
        """获取常用教师列表"""
        return self.get("common_data.teachers", [])

    def add_common_teacher(self, name: str):
        """添加常用教师"""
        self.add_to_list("common_data.teachers", name)

    def get_common_courses(self) -> list:
        """获取常用课程列表"""
        return self.get("common_data.courses", [])

    def add_common_course(self, name: str):
        """添加常用课程"""
        self.add_to_list("common_data.courses", name)

    def get_window_geometry(self) -> Dict[str, int]:
        """获取窗口几何信息"""
        return self.get("window", {})

    def set_window_geometry(self, x: int, y: int, width: int, height: int):
        """设置窗口几何信息"""
        self.set("window.x", x, save=False)
        self.set("window.y", y, save=False)
        self.set("window.width", width, save=False)
        self.set("window.height", height, save=True)

    def get_template_path(self) -> str:
        """获取模板路径"""
        return self.get("paths.template_path", "templates/课程反馈.pptx")

    def set_template_path(self, path: str):
        """设置模板路径"""
        self.set("paths.template_path", path)

    def get_last_save_path(self) -> str:
        """获取上次保存路径"""
        return self.get("paths.last_save_path", "output")

    def set_last_save_path(self, path: str):
        """设置上次保存路径"""
        self.set("paths.last_save_path", path)

    def get_last_excel_path(self) -> str:
        """获取上次Excel路径"""
        return self.get("paths.last_excel_path", "")

    def set_last_excel_path(self, path: str):
        """设置上次Excel路径"""
        self.set("paths.last_excel_path", path)

    def get_default_class_hours(self) -> int:
        """获取默认课时数"""
        return self.get("common_data.default_class_hours", 2)

    def set_default_class_hours(self, hours: int):
        """设置默认课时数"""
        self.set("common_data.default_class_hours", hours)

    def reset_to_defaults(self):
        """重置为默认配置"""
        self.config = self.DEFAULT_CONFIG.copy()
        self._save()

    def reset_layout_to_defaults(self):
        """重置布局配置为默认值"""
        default_layout = self.DEFAULT_CONFIG["layout_selection"].copy()
        self.set("layout_selection", default_layout)
