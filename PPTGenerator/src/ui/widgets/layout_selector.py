# -*- coding: utf-8 -*-
"""
母版选择组件 (F014)
支持勾选5种母版
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QCheckBox, QLabel, QPushButton
)
from PyQt5.QtCore import pyqtSignal


class LayoutSelectorWidget(QWidget):
    """母版选择组件"""

    # 信号：配置改变
    config_changed = pyqtSignal(dict)

    # 母版信息
    LAYOUTS = [
        ("course_info", "课程信息页", True),
        ("model", "模型展示页", True),
        ("program", "程序展示页", False),
        ("vehicle", "车辆展示页", False),
        ("work", "精彩瞬间", True),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 母版选择组
        group = QGroupBox("母版选择")
        group_layout = QVBoxLayout(group)

        # 创建复选框
        self.checkboxes = {}
        for key, name, default in self.LAYOUTS:
            cb = QCheckBox(name)
            cb.setChecked(default)
            self.checkboxes[key] = cb
            group_layout.addWidget(cb)

        # 恢复默认按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        reset_btn = QPushButton("恢复默认")
        reset_btn.clicked.connect(self._reset_to_defaults)
        btn_layout.addWidget(reset_btn)
        group_layout.addLayout(btn_layout)

        layout.addWidget(group)

    def _connect_signals(self):
        """连接信号"""
        for key, cb in self.checkboxes.items():
            cb.stateChanged.connect(self._on_config_changed)

    def _on_config_changed(self):
        """配置改变时发射信号"""
        self.config_changed.emit(self.get_config())

    def get_config(self) -> dict:
        """获取当前配置"""
        config = {
            "include_course_info": self.checkboxes["course_info"].isChecked(),
            "include_model_display": self.checkboxes["model"].isChecked(),
            "include_work_display": self.checkboxes["work"].isChecked(),
            "include_program_display": self.checkboxes["program"].isChecked(),
            "include_vehicle_display": self.checkboxes["vehicle"].isChecked(),
        }
        return config

    def set_config(self, config: dict):
        """设置配置"""
        self.checkboxes["course_info"].setChecked(config.get("include_course_info", True))
        self.checkboxes["model"].setChecked(config.get("include_model_display", True))
        self.checkboxes["work"].setChecked(config.get("include_work_display", True))
        self.checkboxes["program"].setChecked(config.get("include_program_display", False))
        self.checkboxes["vehicle"].setChecked(config.get("include_vehicle_display", False))

    def _reset_to_defaults(self):
        """重置为默认值"""
        defaults = {
            "include_course_info": True,
            "include_model_display": True,
            "include_work_display": True,
            "include_program_display": False,
            "include_vehicle_display": False,
        }
        self.set_config(defaults)
