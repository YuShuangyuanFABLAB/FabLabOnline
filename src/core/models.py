# -*- coding: utf-8 -*-
"""
数据模型定义
定义课程单元、布局配置等数据类
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Union
from enum import Enum
from datetime import datetime


class EvaluationLevel(Enum):
    """评价等级枚举"""
    EXCELLENT = "优"
    GOOD = "良"
    MEDIUM = "中"
    POOR = "差"
    NOT_SHOWN = "未体现"


class OverallEvaluation(Enum):
    """总体评价枚举"""
    EXCELLENT = "优"
    GOOD = "良"
    NEED_EFFORT = "仍需努力"
    NEED_IMPROVEMENT = "需要改进"


class HomeworkEvaluation(Enum):
    """作业评价枚举"""
    EXCELLENT = "优"
    GOOD = "良"
    MEDIUM = "中"
    POOR = "差"
    NONE = "无"


@dataclass
class CourseUnitData:
    """课程单元数据类"""
    # 基本信息
    lesson_number: int = 1
    course_content: str = ""
    student_name: str = ""
    teacher_name: str = ""
    class_hours: int = 2
    class_date: str = ""

    # 课程内容
    knowledge_content: str = ""
    knowledge_html: str = ""  # 知识内容HTML（保留格式）
    # 重点/难点：支持两种格式
    # 1. 简单字符串列表 ["词汇1", "词汇2"] - 标记第一次出现
    # 2. 元组列表 [("词汇1", 索引), ("词汇2", 索引)] - 标记指定索引的出现（1表示第1次，2表示第2次...）
    highlights: List[Union[str, Tuple[str, int]]] = field(default_factory=list)
    difficulties: List[Union[str, Tuple[str, int]]] = field(default_factory=list)

    # 课堂评价
    logic_thinking: EvaluationLevel = EvaluationLevel.NOT_SHOWN
    content_understanding: EvaluationLevel = EvaluationLevel.NOT_SHOWN
    task_completion: EvaluationLevel = EvaluationLevel.NOT_SHOWN
    listening_habit: EvaluationLevel = EvaluationLevel.NOT_SHOWN
    problem_solving: EvaluationLevel = EvaluationLevel.NOT_SHOWN
    independent_analysis: EvaluationLevel = EvaluationLevel.NOT_SHOWN
    knowledge_proficiency: EvaluationLevel = EvaluationLevel.NOT_SHOWN
    imagination_creativity: EvaluationLevel = EvaluationLevel.NOT_SHOWN
    frustration_handling: EvaluationLevel = EvaluationLevel.NOT_SHOWN
    learning_method: EvaluationLevel = EvaluationLevel.NOT_SHOWN
    hands_on_ability: EvaluationLevel = EvaluationLevel.NOT_SHOWN
    focus_efficiency: EvaluationLevel = EvaluationLevel.NOT_SHOWN

    # 总体评价
    overall_evaluation: OverallEvaluation = OverallEvaluation.GOOD

    # 补充信息
    additional_comments: str = ""
    homework: str = ""
    other_notes: str = ""
    last_homework_status: HomeworkEvaluation = HomeworkEvaluation.NONE

    # 图片路径
    model_images: List[str] = field(default_factory=list)
    work_images: List[str] = field(default_factory=list)
    program_images: List[str] = field(default_factory=list)
    vehicle_images: List[str] = field(default_factory=list)


@dataclass
class LayoutConfig:
    """母版配置类"""
    include_course_info: bool = True
    include_model_display: bool = True
    model_display_count: int = 1
    include_double_image: bool = False
    include_program_display: bool = False
    include_vehicle_display: bool = False
    include_work_display: bool = True

    def get_total_pages(self, model_image_count: int = 1, work_image_count: int = 1,
                        program_image_count: int = 1, vehicle_image_count: int = 1) -> int:
        """
        计算总页数

        Args:
            model_image_count: 模型展示图片数量
            work_image_count: 精彩瞬间图片数量
            program_image_count: 程序展示图片数量
            vehicle_image_count: 车辆展示图片数量
        """
        count = 0
        if self.include_course_info:
            count += 1
        if self.include_model_display:
            count += model_image_count
        if self.include_program_display:
            count += program_image_count
        if self.include_vehicle_display:
            count += vehicle_image_count
        if self.include_work_display:
            count += work_image_count
        return count


@dataclass
class ImageData:
    """图片数据类"""
    path: str
    target_width: float = 6.55  # 英寸
    target_height: float = 8.07  # 英寸
    crop_mode: str = "center"  # center, manual
    crop_x: float = 0.0
    crop_y: float = 0.0
    rotation: int = 0
