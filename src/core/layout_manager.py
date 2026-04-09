# -*- coding: utf-8 -*-
"""
布局管理器
负责管理母版布局的选择和应用
"""

from typing import Dict, List, Optional, Any
from dataclasses import asdict

from .models import LayoutConfig


class LayoutManager:
    """布局管理器类"""

    # 所有可用的布局类型
    LAYOUT_TYPES = {
        "course_info": {
            "name": "课程信息页",
            "description": "包含课程内容、评价等信息",
            "max_count": 1,
            "icon": "📋"
        },
        "model": {
            "name": "模型展示页",
            "description": "展示模型图片",
            "max_count": None,  # 无限制
            "icon": "🏗️"
        },
        "double_image": {
            "name": "精彩瞬间(双图)",
            "description": "并排展示两张图片",
            "max_count": 1,
            "icon": "📷"
        },
        "program": {
            "name": "程序展示页",
            "description": "展示程序截图",
            "max_count": 1,
            "icon": "💻"
        },
        "vehicle": {
            "name": "车辆展示页",
            "description": "展示车辆模型",
            "max_count": 1,
            "icon": "🚗"
        },
        "work": {
            "name": "作品展示页",
            "description": "展示学生作品",
            "max_count": 1,
            "icon": "🖼️"
        }
    }

    def __init__(self):
        """初始化布局管理器"""
        self.config = LayoutConfig()

    def set_config(self, config: LayoutConfig):
        """设置布局配置"""
        self.config = config

    def set_config_from_dict(self, config_dict: Dict[str, Any]):
        """
        从字典设置布局配置

        Args:
            config_dict: 配置字典
        """
        self.config = LayoutConfig(
            include_course_info=config_dict.get("include_course_info", True),
            include_model_display=config_dict.get("include_model_display", True),
            model_display_count=config_dict.get("model_display_count", 1),
            include_double_image=config_dict.get("include_double_image", False),
            include_program_display=config_dict.get("include_program_display", False),
            include_vehicle_display=config_dict.get("include_vehicle_display", False),
            include_work_display=config_dict.get("include_work_display", True)
        )

    def get_config(self) -> LayoutConfig:
        """获取当前布局配置"""
        return self.config

    def get_config_dict(self) -> Dict[str, Any]:
        """获取当前布局配置（字典格式）"""
        return asdict(self.config)

    def get_layout_sequence(self) -> List[str]:
        """
        获取布局顺序列表

        Returns:
            布局键名列表
        """
        sequence = []

        if self.config.include_course_info:
            sequence.append("course_info")

        for _ in range(self.config.model_display_count):
            sequence.append("model")

        if self.config.include_double_image:
            sequence.append("double_image")

        if self.config.include_program_display:
            sequence.append("program")

        if self.config.include_vehicle_display:
            sequence.append("vehicle")

        if self.config.include_work_display:
            sequence.append("work")

        return sequence

    def get_layout_sequence_with_names(self) -> List[Dict[str, str]]:
        """
        获取布局顺序列表（包含名称）

        Returns:
            布局信息列表
        """
        sequence = self.get_layout_sequence()
        result = []

        for key in sequence:
            layout_info = self.LAYOUT_TYPES.get(key, {})
            result.append({
                "key": key,
                "name": layout_info.get("name", key),
                "icon": layout_info.get("icon", "")
            })

        return result

    def get_total_pages(self) -> int:
        """获取总页数（每个课程单元）"""
        return self.config.get_total_pages()

    def get_all_layout_types(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有布局类型

        Returns:
            布局类型字典
        """
        return self.LAYOUT_TYPES.copy()

    def get_layout_type_info(self, layout_key: str) -> Optional[Dict[str, Any]]:
        """
        获取指定布局类型的信息

        Args:
            layout_key: 布局键名

        Returns:
            布局信息字典
        """
        return self.LAYOUT_TYPES.get(layout_key)

    def is_layout_enabled(self, layout_key: str) -> bool:
        """
        检查布局是否启用

        Args:
            layout_key: 布局键名

        Returns:
            是否启用
        """
        enabled_map = {
            "course_info": self.config.include_course_info,
            "model": self.config.include_model_display,
            "double_image": self.config.include_double_image,
            "program": self.config.include_program_display,
            "vehicle": self.config.include_vehicle_display,
            "work": self.config.include_work_display
        }
        return enabled_map.get(layout_key, False)

    def set_layout_enabled(self, layout_key: str, enabled: bool):
        """
        设置布局启用状态

        Args:
            layout_key: 布局键名
            enabled: 是否启用
        """
        if layout_key == "course_info":
            self.config.include_course_info = enabled
        elif layout_key == "model":
            self.config.include_model_display = enabled
        elif layout_key == "double_image":
            self.config.include_double_image = enabled
        elif layout_key == "program":
            self.config.include_program_display = enabled
        elif layout_key == "vehicle":
            self.config.include_vehicle_display = enabled
        elif layout_key == "work":
            self.config.include_work_display = enabled

    def set_model_count(self, count: int):
        """
        设置模型展示页数量

        Args:
            count: 数量 (1-10)
        """
        self.config.model_display_count = max(0, min(10, count))

    def reset_to_defaults(self):
        """重置为默认配置"""
        self.config = LayoutConfig()

    @classmethod
    def get_default_config(cls) -> LayoutConfig:
        """获取默认配置"""
        return LayoutConfig()
