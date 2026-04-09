# -*- coding: utf-8 -*-
"""
批量生成模块 (F025)
支持批量生成多个课程反馈PPT
"""

import os
from pathlib import Path
from typing import List, Callable, Optional
from dataclasses import dataclass
from datetime import datetime

from src.core.models import CourseUnitData, LayoutConfig
from src.core.ppt_generator import PPTGenerator


@dataclass
class BatchTask:
    """批量任务"""
    index: int
    data: CourseUnitData
    series_name: str = ""
    series_level: int = 0
    status: str = "pending"  # pending, processing, success, failed
    output_path: str = ""
    error: str = ""


@dataclass
class BatchResult:
    """批量生成结果"""
    total: int
    success: int
    failed: int
    tasks: List[BatchTask]
    output_dir: str


class BatchGenerator:
    """批量生成器"""

    def __init__(self, template_path: str):
        self.template_path = template_path
        self._tasks: List[BatchTask] = []
        self._progress_callback: Optional[Callable] = None
        self._is_cancelled = False

    def set_progress_callback(self, callback: Callable):
        """设置进度回调函数"""
        self._progress_callback = callback

    def add_task(self, data: CourseUnitData, series_name: str = "", series_level: int = 0):
        """添加任务"""
        task = BatchTask(
            index=len(self._tasks),
            data=data,
            series_name=series_name,
            series_level=series_level
        )
        self._tasks.append(task)

    def add_tasks(self, data_list: List[CourseUnitData]):
        """批量添加任务"""
        for data in data_list:
            self.add_task(data)

    def clear_tasks(self):
        """清空任务"""
        self._tasks = []

    def get_task_count(self) -> int:
        """获取任务数量"""
        return len(self._tasks)

    def cancel(self):
        """取消生成"""
        self._is_cancelled = True

    def generate_all(
        self,
        output_dir: str,
        layout_config: LayoutConfig = None,
        overwrite: bool = True
    ) -> BatchResult:
        """
        批量生成所有PPT

        Args:
            output_dir: 输出目录
            layout_config: 布局配置
            overwrite: 是否覆盖已存在文件

        Returns:
            BatchResult: 生成结果
        """
        self._is_cancelled = False

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 默认配置
        if layout_config is None:
            layout_config = LayoutConfig()

        success_count = 0
        failed_count = 0

        for task in self._tasks:
            if self._is_cancelled:
                task.status = "cancelled"
                continue

            task.status = "processing"

            # 回调进度
            if self._progress_callback:
                self._progress_callback(task.index + 1, len(self._tasks), task.data.student_name)

            try:
                # 生成单个PPT
                generator = PPTGenerator(self.template_path)

                # 计算图片数量（勾选且图片存在才生成页面）
                model_image_count = len(task.data.model_images) if task.data.model_images and layout_config.include_model_display else 0
                work_image_count = len(task.data.work_images) if task.data.work_images and layout_config.include_work_display else 0
                program_image_count = len(task.data.program_images) if task.data.program_images and layout_config.include_program_display else 0
                vehicle_image_count = len(task.data.vehicle_images) if task.data.vehicle_images and layout_config.include_vehicle_display else 0

                # 判断是否为第1课（第1课包含封面，其他课不包含）
                include_cover = (task.data.lesson_number == 1)

                # 根据配置生成（传递图片数量）
                generator.generate_from_template(
                    layout_config,
                    model_image_count=model_image_count,
                    work_image_count=work_image_count,
                    program_image_count=program_image_count,
                    vehicle_image_count=vehicle_image_count,
                    include_cover=include_cover
                )

                # 填充内容（传递系列信息和图片数量）
                from src.core.content_filler import fill_ppt_content
                fill_ppt_content(
                    generator.prs, task.data,
                    task.series_name, task.series_level,
                    model_image_count=model_image_count,
                    work_image_count=work_image_count,
                    program_image_count=program_image_count,
                    vehicle_image_count=vehicle_image_count,
                    include_cover=include_cover
                )

                # 保存
                success, path = generator.save_course_unit(output_dir, task.data, overwrite)

                if success:
                    # 计算课程信息页索引（1-based）
                    # include_cover=True: 课程信息页是第2页
                    # include_cover=False: 课程信息页是第1页
                    course_info_slide_index = 2 if include_cover else 1

                    # 后处理：一次性完成高度调整和纵向分布（只打开 PPT 一次）
                    from src.core.content_filler import post_process_ppt
                    try:
                        post_process_ppt(path, course_info_slide_index, keep_open=True)
                    except Exception as post_error:
                        # 后处理失败不影响主流程，只记录警告
                        print(f"警告: 后处理失败 - {post_error}")

                    task.status = "success"
                    task.output_path = path
                    success_count += 1
                else:
                    task.status = "failed"
                    task.error = "保存失败"
                    failed_count += 1

            except Exception as e:
                task.status = "failed"
                task.error = str(e)
                failed_count += 1

        return BatchResult(
            total=len(self._tasks),
            success=success_count,
            failed=failed_count,
            tasks=self._tasks,
            output_dir=output_dir
        )

    def generate_single(
        self,
        data: CourseUnitData,
        output_dir: str,
        layout_config: LayoutConfig = None,
        overwrite: bool = True
    ) -> tuple:
        """
        生成单个PPT

        Returns:
            (success, output_path)
        """
        if layout_config is None:
            layout_config = LayoutConfig()

        try:
            generator = PPTGenerator(self.template_path)
            generator.generate_from_template(layout_config)

            # TODO: 填充内容

            return generator.save_course_unit(output_dir, data, overwrite)

        except Exception as e:
            print(f"生成失败: {e}")
            return False, ""
