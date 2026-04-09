# -*- coding: utf-8 -*-
"""
Excel导入对话框 (F022)
支持数据预览和行选择
"""

from typing import List, Optional
from pathlib import Path

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableView, QAbstractItemView,
    QPushButton, QLabel, QFileDialog, QMessageBox, QHeaderView,
    QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QStandardItemModel, QStandardItem

from src.core.excel_importer import ExcelImporter, ExcelImportResult
from src.core.models import CourseUnitData


class ExcelImportDialog(QDialog):
    """Excel导入对话框"""

    data_imported = pyqtSignal(list)  # 导入完成信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self._importer = ExcelImporter()
        self._import_result: Optional[ExcelImportResult] = None
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("导入Excel数据")
        self.setMinimumSize(900, 600)

        layout = QVBoxLayout(self)

        # 顶部：文件选择
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("文件:"))

        self.file_path_label = QLabel("未选择文件")
        self.file_path_label.setStyleSheet("color: #666;")
        file_layout.addWidget(self.file_path_label, 1)

        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._on_browse)
        file_layout.addWidget(browse_btn)

        layout.addLayout(file_layout)

        # 中部：数据预览表格
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels([
            "选择", "课时", "课程内容", "学生姓名", "授课教师", "总体评价"
        ])
        self.table_view.setModel(self.model)

        # 设置列宽
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_view.setColumnWidth(0, 50)
        self.table_view.setColumnWidth(1, 50)
        self.table_view.setColumnWidth(3, 100)
        self.table_view.setColumnWidth(4, 100)
        self.table_view.setColumnWidth(5, 80)

        layout.addWidget(self.table_view)

        # 状态信息
        self.status_label = QLabel("请选择Excel文件")
        layout.addWidget(self.status_label)

        # 底部：按钮
        btn_layout = QHBoxLayout()

        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(self._on_select_all)
        btn_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("取消全选")
        deselect_all_btn.clicked.connect(self._on_deselect_all)
        btn_layout.addWidget(deselect_all_btn)

        btn_layout.addStretch()

        self.import_btn = QPushButton("导入选中")
        self.import_btn.setEnabled(False)
        self.import_btn.clicked.connect(self._on_import)
        btn_layout.addWidget(self.import_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _on_browse(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Excel文件",
            "",
            "Excel文件 (*.xlsx *.xls);;所有文件 (*)"
        )

        if file_path:
            self._load_file(file_path)

    def _load_file(self, file_path: str):
        """加载Excel文件"""
        # 验证文件
        valid, msg = self._importer.validate_file(file_path)
        if not valid:
            QMessageBox.warning(self, "错误", msg)
            return

        self.file_path_label.setText(Path(file_path).name)
        self.file_path_label.setStyleSheet("color: #000;")

        # 导入数据
        self._import_result = self._importer.import_from_file(file_path)

        if not self._import_result.success:
            QMessageBox.warning(self, "错误", "文件导入失败")
            return

        # 显示错误
        if self._import_result.errors:
            error_msg = "\n".join(self._import_result.errors[:5])
            if len(self._import_result.errors) > 5:
                error_msg += f"\n... 还有{len(self._import_result.errors) - 5}个错误"
            QMessageBox.warning(self, "警告", f"部分数据有问题:\n{error_msg}")

        # 更新表格
        self._update_table()

        # 更新状态
        self.status_label.setText(
            f"共{self._import_result.row_count}行，"
            f"有效{self._import_result.valid_count}行"
        )

        self.import_btn.setEnabled(self._import_result.valid_count > 0)

    def _update_table(self):
        """更新表格"""
        self.model.removeRows(0, self.model.rowCount())

        if not self._import_result or not self._import_result.data:
            return

        for data in self._import_result.data:
            # 复选框
            check_item = QStandardItem()
            check_item.setCheckable(True)
            check_item.setCheckState(Qt.Checked)

            # 数据
            row = [
                check_item,
                QStandardItem(str(data.lesson_number)),
                QStandardItem(data.course_content[:50] + "..." if len(data.course_content) > 50 else data.course_content),
                QStandardItem(data.student_name),
                QStandardItem(data.teacher_name),
                QStandardItem(data.overall_evaluation.value if data.overall_evaluation else ""),
            ]

            self.model.appendRow(row)

    def _on_select_all(self):
        """全选"""
        for row in range(self.model.rowCount()):
            self.model.item(row, 0).setCheckState(Qt.Checked)

    def _on_deselect_all(self):
        """取消全选"""
        for row in range(self.model.rowCount()):
            self.model.item(row, 0).setCheckState(Qt.Unchecked)

    def _on_import(self):
        """导入选中数据"""
        selected_data = []

        for row in range(self.model.rowCount()):
            if self.model.item(row, 0).checkState() == Qt.Checked:
                if row < len(self._import_result.data):
                    selected_data.append(self._import_result.data[row])

        if not selected_data:
            QMessageBox.warning(self, "警告", "请选择要导入的数据")
            return

        self.data_imported.emit(selected_data)
        self.accept()

    def get_selected_data(self) -> List[CourseUnitData]:
        """获取选中的数据"""
        selected_data = []

        for row in range(self.model.rowCount()):
            if self.model.item(row, 0).checkState() == Qt.Checked:
                if row < len(self._import_result.data):
                    selected_data.append(self._import_result.data[row])

        return selected_data
