# -*- coding: utf-8 -*-
"""
表单数据序列化模块 (F023)
支持表单数据的保存和加载
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import asdict

from src.core.models import (
    CourseUnitData, LayoutConfig,
    EvaluationLevel, OverallEvaluation, HomeworkEvaluation
)


class FormSerializer:
    """表单数据序列化器"""

    @staticmethod
    def serialize(data: CourseUnitData, layout_config: LayoutConfig = None) -> Dict[str, Any]:
        """序列化课程数据"""
        result = {
            "version": "1.0",
            "saved_at": datetime.now().isoformat(),
            "data": {}
        }

        # 基本信息
        result["data"]["lesson_number"] = data.lesson_number
        result["data"]["course_content"] = data.course_content
        result["data"]["student_name"] = data.student_name
        result["data"]["teacher_name"] = data.teacher_name
        result["data"]["class_hours"] = data.class_hours
        result["data"]["class_date"] = data.class_date

        # 评价
        eval_fields = [
            "logic_thinking", "content_understanding", "task_completion",
            "listening_habit", "problem_solving", "independent_analysis",
            "knowledge_proficiency", "imagination_creativity", "frustration_handling",
            "learning_method", "hands_on_ability", "focus_efficiency"
        ]

        for field in eval_fields:
            value = getattr(data, field, None)
            if value:
                result["data"][field] = value.value

        # 总体评价
        if data.overall_evaluation:
            result["data"]["overall_evaluation"] = data.overall_evaluation.value

        # 上次作业
        if data.last_homework_status:
            result["data"]["last_homework_status"] = data.last_homework_status.value

        # 文本
        result["data"]["additional_comments"] = data.additional_comments
        result["data"]["homework"] = data.homework
        result["data"]["other_notes"] = data.other_notes

        # 图片路径
        result["data"]["model_images"] = data.model_images
        result["data"]["work_images"] = data.work_images
        result["data"]["double_images"] = data.double_images

        # 布局配置
        if layout_config:
            result["layout_config"] = {
                "include_course_info": layout_config.include_course_info,
                "include_model_display": layout_config.include_model_display,
                "model_display_count": layout_config.model_display_count,
                "include_double_image": layout_config.include_double_image,
                "include_program_display": layout_config.include_program_display,
                "include_vehicle_display": layout_config.include_vehicle_display,
                "include_work_display": layout_config.include_work_display,
            }

        return result

    @staticmethod
    def deserialize(data: Dict[str, Any]) -> tuple:
        """反序列化数据"""
        course_data = CourseUnitData()
        layout_config = None

        if "data" not in data:
            return course_data, layout_config

        d = data["data"]

        # 基本信息
        course_data.lesson_number = d.get("lesson_number", 1)
        course_data.course_content = d.get("course_content", "")
        course_data.student_name = d.get("student_name", "")
        course_data.teacher_name = d.get("teacher_name", "")
        course_data.class_hours = d.get("class_hours", 2)
        course_data.class_date = d.get("class_date", "")

        # 评价等级映射
        level_map = {
            "优": EvaluationLevel.EXCELLENT,
            "良": EvaluationLevel.GOOD,
            "中": EvaluationLevel.MEDIUM,
            "差": EvaluationLevel.POOR,
            "未体现": EvaluationLevel.NOT_SHOWN,
        }

        overall_map = {
            "优": OverallEvaluation.EXCELLENT,
            "良": OverallEvaluation.GOOD,
            "仍需努力": OverallEvaluation.NEED_EFFORT,
            "需要改进": OverallEvaluation.NEED_IMPROVEMENT,
        }

        homework_map = {
            "优": HomeworkEvaluation.EXCELLENT,
            "良": HomeworkEvaluation.GOOD,
            "中": HomeworkEvaluation.MEDIUM,
            "差": HomeworkEvaluation.POOR,
            "无": HomeworkEvaluation.NONE,
        }

        # 12项评价
        eval_fields = [
            "logic_thinking", "content_understanding", "task_completion",
            "listening_habit", "problem_solving", "independent_analysis",
            "knowledge_proficiency", "imagination_creativity", "frustration_handling",
            "learning_method", "hands_on_ability", "focus_efficiency"
        ]

        for field in eval_fields:
            value = d.get(field)
            if value and value in level_map:
                setattr(course_data, field, level_map[value])

        # 总体评价
        if d.get("overall_evaluation") and d["overall_evaluation"] in overall_map:
            course_data.overall_evaluation = overall_map[d["overall_evaluation"]]

        # 上次作业
        if d.get("last_homework_status") and d["last_homework_status"] in homework_map:
            course_data.last_homework_status = homework_map[d["last_homework_status"]]

        # 文本
        course_data.additional_comments = d.get("additional_comments", "")
        course_data.homework = d.get("homework", "")
        course_data.other_notes = d.get("other_notes", "")

        # 图片
        course_data.model_images = d.get("model_images", [])
        course_data.work_images = d.get("work_images", [])
        course_data.double_images = d.get("double_images", [])

        # 布局配置
        if "layout_config" in data:
            lc = data["layout_config"]
            layout_config = LayoutConfig(
                include_course_info=lc.get("include_course_info", True),
                include_model_display=lc.get("include_model_display", True),
                model_display_count=lc.get("model_display_count", 1),
                include_double_image=lc.get("include_double_image", False),
                include_program_display=lc.get("include_program_display", False),
                include_vehicle_display=lc.get("include_vehicle_display", False),
                include_work_display=lc.get("include_work_display", True),
            )

        return course_data, layout_config

    @staticmethod
    def save_to_file(data: CourseUnitData, layout_config: LayoutConfig, file_path: str) -> bool:
        """保存到文件"""
        try:
            serialized = FormSerializer.serialize(data, layout_config)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(serialized, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            return False

    @staticmethod
    def load_from_file(file_path: str) -> tuple:
        """从文件加载"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return FormSerializer.deserialize(data)
        except Exception as e:
            print(f"加载失败: {e}")
            return CourseUnitData(), None


class RecentFilesManager:
    """最近文件管理器"""

    MAX_FILES = 10

    def __init__(self, config_manager):
        self._config = config_manager

    def add_file(self, file_path: str, student_name: str = ""):
        """添加最近文件"""
        recent = self._config.get("recent_files", [])

        # 创建条目
        entry = {
            "path": file_path,
            "name": student_name or Path(file_path).stem,
            "time": datetime.now().isoformat()
        }

        # 移除旧条目
        recent = [r for r in recent if r.get("path") != file_path]

        # 添加到开头
        recent.insert(0, entry)

        # 限制数量
        recent = recent[:self.MAX_FILES]

        self._config.set("recent_files", recent)
        self._config.save_settings()

    def get_recent_files(self) -> List[Dict[str, str]]:
        """获取最近文件列表"""
        recent = self._config.get("recent_files", [])
        # 过滤存在的文件
        recent = [r for r in recent if Path(r.get("path", "")).exists()]
        return recent

    def clear(self):
        """清空最近文件"""
        self._config.set("recent_files", [])
        self._config.save_settings()
