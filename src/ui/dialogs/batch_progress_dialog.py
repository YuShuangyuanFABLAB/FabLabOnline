# -*- coding: utf-8 -*-
"""
批量生成进度对话框
显示批量生成的进度和结果
"""

from typing import List

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor

from src.core.models import CourseUnitData, LayoutConfig
from src.core.batch_generator import BatchGenerator, BatchResult, BatchTask


class BatchGenerateThread(QThread):
    """批量生成线程"""

    progress = pyqtSignal(int, int, str)  # current, total, student_name
    finished = pyqtSignal(object)  # BatchResult

    def __init__(
        self,
        generator: BatchGenerator,
        output_dir: str,
        layout_config: LayoutConfig
    ):
        super().__init__()
        self._generator = generator
        self._output_dir = output_dir
        self._layout_config = layout_config

    def run(self):
        self._generator.set_progress_callback(self._on_progress)
        result = self._generator.generate_all(
            self._output_dir,
            self._layout_config
        )
        self.finished.emit(result)

    def _on_progress(self, current: int, total: int, name: str):
        self.progress.emit(current, total, name)

    def cancel(self):
        self._generator.cancel()


class BatchProgressDialog(QDialog):
    """批量生成进度对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: BatchGenerateThread = None
        self._result = None
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("批量生成PPT")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)

        # 进度信息
        self.status_label = QLabel("准备生成...")
        layout.addWidget(self.status_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # 当前处理
        self.current_label = QLabel("")
        layout.addWidget(self.current_label)

        # 结果表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["学生姓名", "状态", "输出路径", "错误信息"])
        self.result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.result_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.result_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.result_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.result_table.setVisible(False)
        layout.addWidget(self.result_table)

        # 统计信息
        self.stats_label = QLabel("")
        self.stats_label.setVisible(False)
        layout.addWidget(self.stats_label)

        # 按钮
        btn_layout = QHBoxLayout()

        self.open_dir_btn = QPushButton("打开输出目录")
        self.open_dir_btn.setVisible(False)
        self.open_dir_btn.clicked.connect(self._on_open_dir)
        btn_layout.addWidget(self.open_dir_btn)

        btn_layout.addStretch()

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self.cancel_btn)

        self.close_btn = QPushButton("关闭")
        self.close_btn.setVisible(False)
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

    def start_generation(
        self,
        data_list: List[CourseUnitData],
        output_dir: str,
        template_path: str,
        layout_config: LayoutConfig = None,
        series_name: str = "",
        series_level: int = 0
    ):
        """开始批量生成"""
        if layout_config is None:
            layout_config = LayoutConfig()

        # 创建生成器
        generator = BatchGenerator(template_path)
        for data in data_list:
            generator.add_task(data, series_name, series_level)

        # 创建线程
        self._thread = BatchGenerateThread(generator, output_dir, layout_config)
        self._thread.progress.connect(self._on_progress)
        self._thread.finished.connect(self._on_finished)

        # 更新UI
        self.status_label.setText(f"准备生成 {len(data_list)} 个课程反馈...")
        self.progress_bar.setMaximum(len(data_list))
        self.progress_bar.setValue(0)

        # 开始
        self._thread.start()

    def _on_progress(self, current: int, total: int, name: str):
        """进度更新"""
        self.progress_bar.setValue(current)
        self.progress_bar.setMaximum(total)
        self.current_label.setText(f"正在处理: {name}")
        self.status_label.setText(f"生成进度: {current}/{total}")

    def _on_finished(self, result: BatchResult):
        """生成完成"""
        self._result = result

        # 更新UI
        self.status_label.setText("生成完成")
        self.current_label.setVisible(False)
        self.progress_bar.setValue(result.total)

        # 显示结果
        self._show_results(result)

        # 切换按钮
        self.cancel_btn.setVisible(False)
        self.close_btn.setVisible(True)
        self.open_dir_btn.setVisible(True)

    def _show_results(self, result: BatchResult):
        """显示结果"""
        self.result_table.setVisible(True)
        self.result_table.setRowCount(len(result.tasks))

        for i, task in enumerate(result.tasks):
            # 学生姓名
            self.result_table.setItem(i, 0, QTableWidgetItem(task.data.student_name))

            # 状态
            status_item = QTableWidgetItem(
                "成功" if task.status == "success" else
                "失败" if task.status == "failed" else
                "取消"
            )
            if task.status == "success":
                status_item.setBackground(QColor(200, 255, 200))
            elif task.status == "failed":
                status_item.setBackground(QColor(255, 200, 200))
            self.result_table.setItem(i, 1, status_item)

            # 输出路径
            self.result_table.setItem(i, 2, QTableWidgetItem(task.output_path))

            # 错误信息
            self.result_table.setItem(i, 3, QTableWidgetItem(task.error))

        # 统计
        self.stats_label.setVisible(True)
        self.stats_label.setText(
            f"总计: {result.total} | 成功: {result.success} | 失败: {result.failed}"
        )

    def _on_cancel(self):
        """取消"""
        if self._thread and self._thread.isRunning():
            reply = QMessageBox.question(
                self, "确认取消",
                "确定要取消生成吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._thread.cancel()
                self.status_label.setText("正在取消...")

    def _on_open_dir(self):
        """打开输出目录"""
        if self._result:
            import os
            import subprocess
            import platform

            path = self._result.output_dir
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])

    def closeEvent(self, event):
        """关闭事件"""
        if self._thread and self._thread.isRunning():
            reply = QMessageBox.question(
                self, "确认关闭",
                "正在生成中，确定要关闭吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return

            self._thread.cancel()
            self._thread.wait()

        event.accept()

    def get_result(self):
        """获取生成结果"""
        return self._result
