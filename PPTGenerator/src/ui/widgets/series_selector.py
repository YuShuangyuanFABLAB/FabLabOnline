# -*- coding: utf-8 -*-
"""
课程系列选择器组件
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QDialog, QFormLayout, QLineEdit,
    QMessageBox
)
from PyQt5.QtCore import pyqtSignal

from src.ui.widgets.arrow_spinbox import ArrowSpinBox


class AddSeriesDialog(QDialog):
    """添加新系列的对话框"""

    # 最大系列名称长度
    MAX_NAME_LENGTH = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加课程系列")
        self.setModal(True)
        self.setMinimumWidth(300)

        self._init_ui()

    def _init_ui(self):
        layout = QFormLayout(self)

        # 系列名称
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("如：机械臂设计")
        self.name_edit.setMaxLength(self.MAX_NAME_LENGTH)  # 限制输入长度
        self.name_edit.textChanged.connect(self._on_text_changed)
        layout.addRow("系列名称:", self.name_edit)

        # 字数提示
        self.char_count_label = QLabel(f"0/{self.MAX_NAME_LENGTH} 字")
        self.char_count_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addRow("", self.char_count_label)

        # 阶数
        self.level_spin = ArrowSpinBox()
        self.level_spin.setRange(1, 10)
        self.level_spin.setValue(1)
        layout.addRow("阶数:", self.level_spin)

        # 按钮
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self._on_accept)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addRow(btn_layout)

    def _on_text_changed(self, text):
        """文本改变时更新字数提示"""
        length = len(text)
        self.char_count_label.setText(f"{length}/{self.MAX_NAME_LENGTH} 字")
        if length > self.MAX_NAME_LENGTH:
            self.char_count_label.setStyleSheet("color: red; font-size: 10px;")
        else:
            self.char_count_label.setStyleSheet("color: #666; font-size: 10px;")

    def _on_accept(self):
        """确定按钮点击"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入系列名称")
            return
        if len(name) > self.MAX_NAME_LENGTH:
            QMessageBox.warning(self, "提示", f"系列名称不能超过{self.MAX_NAME_LENGTH}个字")
            return
        self.accept()

    def get_series_info(self):
        """获取输入的系列信息"""
        name = self.name_edit.text().strip()
        level = self.level_spin.value()
        return name, level


class SeriesSelectorWidget(QWidget):
    """课程系列选择器"""

    # 系列改变信号，传递 (系列名称, 阶数)
    series_changed = pyqtSignal(str, int)

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self._programmatic_change = False  # 用于区分程序切换和用户操作
        self._init_ui()
        self._load_series()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        title_label = QLabel("班级信息")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)

        # 提示
        hint_label = QLabel("选择课程系列，生成PPT时会自动填充到模板中")
        hint_label.setStyleSheet("color: #666; font-size: 11px;")
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)

        # 系列选择行
        select_layout = QHBoxLayout()

        self.series_combo = QComboBox()
        self.series_combo.setMinimumWidth(200)
        self.series_combo.currentIndexChanged.connect(self._on_series_changed)
        select_layout.addWidget(self.series_combo, 1)

        # 添加按钮
        self.add_btn = QPushButton("添加系列")
        self.add_btn.clicked.connect(self._on_add_series)
        select_layout.addWidget(self.add_btn)

        # 删除按钮
        self.remove_btn = QPushButton("删除")
        self.remove_btn.clicked.connect(self._on_remove_series)
        select_layout.addWidget(self.remove_btn)

        layout.addLayout(select_layout)

        # 当前系列详情
        self.detail_label = QLabel()
        self.detail_label.setStyleSheet("color: #0070C0; font-size: 12px; padding: 5px;")
        layout.addWidget(self.detail_label)

        # 弹性空间
        layout.addStretch()

    def _load_series(self):
        """加载系列列表"""
        series_list = self.config_manager.get_course_series()
        current_index = self.config_manager._settings.get("current_series_index", 0)

        self.series_combo.blockSignals(True)
        self.series_combo.clear()

        for series in series_list:
            name = series.get("name", "")
            level = series.get("level", 1)
            display_name = f"{name} ({level}阶)"
            self.series_combo.addItem(display_name)

        # 恢复选择
        if 0 <= current_index < len(series_list):
            self.series_combo.setCurrentIndex(current_index)

        self.series_combo.blockSignals(False)

        # 更新详情
        self._update_detail()

    def _update_detail(self):
        """更新详情显示"""
        current = self.config_manager.get_current_series()
        name = current.get("name", "")
        level = current.get("level", 1)
        self.detail_label.setText(f"当前选择: {name}（{level}阶）")

    def _on_series_changed(self, index):
        """系列选择改变"""
        if index >= 0:
            self.config_manager.set_current_series(index)
            self._update_detail()
            # 只有用户手动操作才发送信号
            if not self._programmatic_change:
                name, level = self.get_current_series()
                self.series_changed.emit(name, level)

    def _on_add_series(self):
        """添加新系列"""
        dialog = AddSeriesDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            name, level = dialog.get_series_info()

            if not name:
                QMessageBox.warning(self, "提示", "请输入系列名称")
                return

            if self.config_manager.add_course_series(name, level):
                self._load_series()
                # 选中新添加的系列
                series_list = self.config_manager.get_course_series()
                self.series_combo.setCurrentIndex(len(series_list) - 1)
                QMessageBox.information(self, "成功", f"已添加: {name}（{level}阶）")
            else:
                QMessageBox.warning(self, "提示", "该系列已存在")

    def _on_remove_series(self):
        """删除当前系列"""
        index = self.series_combo.currentIndex()
        if index < 0:
            return

        series_list = self.config_manager.get_course_series()
        if len(series_list) <= 1:
            QMessageBox.warning(self, "提示", "至少需要保留一个系列")
            return

        current = series_list[index]
        name = current.get("name", "")
        level = current.get("level", 1)

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除 \"{name}（{level}阶）\" 吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.config_manager.remove_course_series(index)
            self._load_series()
            QMessageBox.information(self, "成功", "已删除")

    def get_current_series(self):
        """获取当前选择的系列信息

        Returns:
            tuple: (名称, 阶数)
        """
        current = self.config_manager.get_current_series()
        return current.get("name", ""), current.get("level", 1)

    def set_series_silently(self, index: int):
        """
        静默切换系列（不触发用户操作信号）

        Args:
            index: 系列索引
        """
        if 0 <= index < self.series_combo.count():
            self._programmatic_change = True
            self.series_combo.setCurrentIndex(index)
            self._programmatic_change = False

    def refresh_series_list(self):
        """刷新系列列表（供外部调用）"""
        self._load_series()
