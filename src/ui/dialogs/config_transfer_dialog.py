# -*- coding: utf-8 -*-
"""
配置导出/导入选择对话框
支持选择性导出和导入班级等配置数据
"""

from typing import Dict, Any, Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QTableView,
    QAbstractItemView, QPushButton, QLabel, QHeaderView,
    QCheckBox, QComboBox, QMessageBox, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from src.core.config_manager import ConfigManager
from src.ui.theme import ThemeManager


class ConfigTransferDialog(QDialog):
    """配置导出/导入选择对话框"""

    MODE_EXPORT = "export"
    MODE_IMPORT = "import"

    def __init__(self, mode: str, config_manager: ConfigManager,
                 import_file_path: str = None, parent=None):
        super().__init__(parent)
        self._mode = mode
        self._config_manager = config_manager
        self._import_file_path = import_file_path
        self._import_data: Optional[Dict[str, Any]] = None
        self._conflict_combos: Dict[str, QComboBox] = {}
        self._theme_colors = ThemeManager.instance().get_colors()

        self._init_ui()
        self._apply_theme()
        self._load_data()

    def _init_ui(self):
        """初始化界面"""
        if self._mode == self.MODE_EXPORT:
            self.setWindowTitle("选择性导出配置")
        else:
            self.setWindowTitle("选择性导入配置")

        self.setMinimumSize(550, 450)
        layout = QVBoxLayout(self)

        # 导入模式：文件摘要
        if self._mode == self.MODE_IMPORT:
            self._summary_label = QLabel("正在读取文件...")
            self._summary_label.setStyleSheet(f"color: {self._theme_colors.text_secondary}; margin-bottom: 5px;")
            layout.addWidget(self._summary_label)

        # 班级选择区域
        class_group = QGroupBox("选择班级")
        class_layout = QVBoxLayout(class_group)

        # 全选/取消全选按钮
        btn_row = QHBoxLayout()
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(self._on_select_all)
        btn_row.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("取消全选")
        deselect_all_btn.clicked.connect(self._on_deselect_all)
        btn_row.addWidget(deselect_all_btn)
        btn_row.addStretch()
        class_layout.addLayout(btn_row)

        # 表格
        self._table = QTableView()
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self._model = QStandardItemModel()
        self._model.setHorizontalHeaderLabels(["选择", "班级名称", "教师", "学员数"])
        self._table.setModel(self._model)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self._table.setColumnWidth(0, 50)
        self._table.setColumnWidth(2, 100)
        self._table.setColumnWidth(3, 70)

        class_layout.addWidget(self._table)
        layout.addWidget(class_group)

        # 其他数据选项
        other_group = QGroupBox("其他数据")
        other_layout = QGridLayout(other_group)

        self._series_check = QCheckBox("课程系列")
        self._series_check.setChecked(True)
        other_layout.addWidget(self._series_check, 0, 0)

        self._colors_check = QCheckBox("颜色配置")
        self._colors_check.setChecked(True)
        other_layout.addWidget(self._colors_check, 0, 1)

        self._recent_check = QCheckBox("最近使用记录（学生/教师/课程）")
        self._recent_check.setChecked(False)
        other_layout.addWidget(self._recent_check, 1, 0)

        self._defaults_check = QCheckBox("默认值（老师/注意事项/主题）")
        self._defaults_check.setChecked(False)
        other_layout.addWidget(self._defaults_check, 1, 1)

        layout.addWidget(other_group)

        # 导入模式：冲突处理区域
        if self._mode == self.MODE_IMPORT:
            self._conflict_group = QGroupBox("班级名称冲突")
            self._conflict_layout = QVBoxLayout(self._conflict_group)
            self._conflict_group.setVisible(False)
            layout.addWidget(self._conflict_group)

        # 底部按钮
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        ok_btn = QPushButton("确认")
        ok_btn.clicked.connect(self._on_confirm)
        bottom_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(cancel_btn)

        layout.addLayout(bottom_layout)

    def _apply_theme(self):
        """应用主题样式"""
        c = self._theme_colors
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {c.background_primary};
                color: {c.text_primary};
            }}
            QGroupBox {{
                color: {c.text_primary};
                border: 1px solid {c.border_normal};
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QTableView {{
                background-color: {c.background_secondary};
                alternate-background-color: {c.background_tertiary};
                color: {c.text_primary};
                gridline-color: {c.border_normal};
                border: 1px solid {c.border_normal};
            }}
            QHeaderView::section {{
                background-color: {c.background_tertiary};
                color: {c.text_primary};
                border: 1px solid {c.border_normal};
                padding: 4px;
            }}
            QCheckBox {{
                color: {c.text_primary};
            }}
            QPushButton {{
                background-color: {c.button_normal};
                color: {c.text_primary};
                border: 1px solid {c.border_normal};
                border-radius: 4px;
                padding: 5px 16px;
            }}
            QPushButton:hover {{
                background-color: {c.border_hover};
            }}
            QComboBox {{
                background-color: {c.background_secondary};
                color: {c.text_primary};
                border: 1px solid {c.border_normal};
                border-radius: 3px;
                padding: 2px 6px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {c.background_secondary};
                color: {c.text_primary};
                selection-background-color: {c.primary};
            }}
        """)

    def _load_data(self):
        """加载数据到表格"""
        if self._mode == self.MODE_EXPORT:
            self._load_export_data()
        else:
            self._load_import_data()

    def _load_export_data(self):
        """从当前配置加载班级列表"""
        classes = self._config_manager.get_classes()
        students_by_class = self._config_manager.settings.get("students_by_class", {})
        series_count = len(self._config_manager.settings.get("course_series", []))

        self._populate_table(classes, students_by_class)
        self._series_check.setText(f"课程系列 ({series_count}个)")

    def _load_import_data(self):
        """从导入文件加载班级列表"""
        self._import_data = self._config_manager.read_config_file(self._import_file_path)
        if not self._import_data:
            self._summary_label.setText("无法读取配置文件或文件格式无效")
            self._summary_label.setStyleSheet("color: red;")
            return

        imported_settings = self._import_data.get("settings", {})
        classes = imported_settings.get("classes", [])
        students_by_class = imported_settings.get("students_by_class", {})
        colors = self._import_data.get("colors", {})
        series = imported_settings.get("course_series", [])

        # 更新摘要
        parts = [f"{len(classes)} 个班级"]
        if series:
            parts.append(f"{len(series)} 个课程系列")
        if colors:
            parts.append(f"{len(colors)} 个颜色定义")
        self._summary_label.setText(f"文件包含: {', '.join(parts)}")
        self._summary_label.setStyleSheet(f"color: {self._theme_colors.text_primary}; margin-bottom: 5px;")

        self._populate_table(classes, students_by_class)
        self._series_check.setText(f"课程系列 ({len(series)}个)")

        # 检测冲突
        self._check_conflicts(classes)

    def _populate_table(self, classes: list, students_by_class: dict):
        """填充表格数据"""
        self._model.removeRows(0, self._model.rowCount())

        for cls in classes:
            class_id = cls.get("id", "")
            class_name = cls.get("name", "")
            teacher = cls.get("teacher", "")
            student_count = len(students_by_class.get(class_id, []))

            check_item = QStandardItem()
            check_item.setCheckable(True)
            check_item.setCheckState(Qt.Checked)
            # 存储班级ID
            check_item.setData(class_id, Qt.UserRole)

            name_item = QStandardItem(class_name)
            teacher_item = QStandardItem(teacher)
            count_item = QStandardItem(str(student_count))

            self._model.appendRow([check_item, name_item, teacher_item, count_item])

    def _check_conflicts(self, imported_classes: list):
        """检测导入班级与现有班级的名称冲突"""
        existing_names = {
            c.get("name") for c in self._config_manager.get_classes()
        }

        conflicts = []
        for cls in imported_classes:
            if cls.get("name") in existing_names:
                conflicts.append(cls)

        if not conflicts:
            return

        self._conflict_group.setVisible(True)

        # 提示
        tip = QLabel(
            f"以下 {len(conflicts)} 个班级名称与当前配置重复："
        )
        tip.setStyleSheet("color: #d32f2f; font-weight: bold;")
        self._conflict_layout.addWidget(tip)

        for cls in conflicts:
            class_id = cls.get("id", "")
            class_name = cls.get("name", "")
            teacher = cls.get("teacher", "")

            row = QHBoxLayout()
            label = QLabel(f"  {class_name}" + (f"（{teacher}）" if teacher else ""))
            label.setMinimumWidth(180)
            row.addWidget(label)

            combo = QComboBox()
            combo.addItem("创建副本", "copy")
            combo.addItem("跳过", "skip")
            combo.setMinimumWidth(100)
            row.addWidget(combo)
            row.addStretch()

            self._conflict_combos[class_id] = combo
            self._conflict_layout.addLayout(row)

    def _on_select_all(self):
        """全选"""
        for row in range(self._model.rowCount()):
            self._model.item(row, 0).setCheckState(Qt.Checked)

    def _on_deselect_all(self):
        """取消全选"""
        for row in range(self._model.rowCount()):
            self._model.item(row, 0).setCheckState(Qt.Unchecked)

    def _on_confirm(self):
        """确认按钮"""
        selection = self.get_selection()
        if not selection["selected_class_ids"]:
            QMessageBox.warning(self, "提示", "请至少选择一个班级")
            return
        self.accept()

    def get_selection(self) -> Dict[str, Any]:
        """
        获取用户选择结果

        Returns:
            {
                "selected_class_ids": [str],
                "include_course_series": bool,
                "include_colors": bool,
                "include_recent": bool,
                "include_defaults": bool,
                "conflict_resolutions": {class_id: "copy"/"skip"}  # 导入模式
            }
        """
        selected_ids = []
        for row in range(self._model.rowCount()):
            item = self._model.item(row, 0)
            if item.checkState() == Qt.Checked:
                class_id = item.data(Qt.UserRole)
                if class_id:
                    selected_ids.append(class_id)

        result = {
            "selected_class_ids": selected_ids,
            "include_course_series": self._series_check.isChecked(),
            "include_colors": self._colors_check.isChecked(),
            "include_recent": self._recent_check.isChecked(),
            "include_defaults": self._defaults_check.isChecked(),
        }

        # 导入模式：冲突处理
        if self._mode == self.MODE_IMPORT:
            resolutions = {}
            for class_id, combo in self._conflict_combos.items():
                resolutions[class_id] = combo.currentData()
            result["conflict_resolutions"] = resolutions

        return result
