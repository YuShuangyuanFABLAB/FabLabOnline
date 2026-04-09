# -*- coding: utf-8 -*-
"""
班级选择器组件
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QDialog, QFormLayout, QLineEdit,
    QMessageBox, QInputDialog
)
from PyQt5.QtCore import pyqtSignal

from src.ui.widgets.arrow_spinbox import ArrowSpinBox


# 星期名称映射
WEEKDAY_NAMES = {
    1: "一", 2: "二", 3: "三", 4: "四",
    5: "五", 6: "六", 7: "日"
}


class AddClassDialog(QDialog):
    """添加班级对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加班级")
        self.setModal(True)
        self.setMinimumWidth(300)

        self._init_ui()

    def _init_ui(self):
        layout = QFormLayout(self)

        # 星期选择
        self.weekday_spin = ArrowSpinBox()
        self.weekday_spin.setRange(1, 7)
        self.weekday_spin.setValue(1)
        self.weekday_spin.setSuffix(" (星期一)")
        self.weekday_spin.valueChanged.connect(self._on_weekday_changed)
        layout.addRow("星期:", self.weekday_spin)

        # 时间选择行
        time_layout = QHBoxLayout()

        self.hour_spin = ArrowSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setValue(14)
        self.hour_spin.setWrapping(True)
        time_layout.addWidget(QLabel("时间:"))
        time_layout.addWidget(self.hour_spin)
        time_layout.addWidget(QLabel(":"))

        self.minute_spin = ArrowSpinBox()
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setValue(0)
        self.minute_spin.setWrapping(True)
        time_layout.addWidget(self.minute_spin)

        layout.addRow("", time_layout)

        # 默认老师输入
        self.teacher_edit = QLineEdit()
        self.teacher_edit.setPlaceholderText("可选，填写默认授课老师")
        layout.addRow("默认老师:", self.teacher_edit)

        # 预览
        self.preview_label = QLabel()
        self.preview_label.setStyleSheet("color: #0070C0; font-weight: bold;")
        self._update_preview()
        layout.addRow("预览:", self.preview_label)

        # 按钮
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self._on_accept)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addRow(btn_layout)

        # 连接信号
        self.hour_spin.valueChanged.connect(self._update_preview)
        self.minute_spin.valueChanged.connect(self._update_preview)

    def _on_weekday_changed(self, value):
        """星期改变时更新显示"""
        self.weekday_spin.setSuffix(f" (星期{WEEKDAY_NAMES[value]})")
        self._update_preview()

    def _update_preview(self):
        """更新预览"""
        name = self.get_class_name()
        self.preview_label.setText(name)

    def get_class_name(self) -> str:
        """获取班级名称"""
        weekday = WEEKDAY_NAMES[self.weekday_spin.value()]
        hour = self.hour_spin.value()
        minute = self.minute_spin.value()
        return f"星期{weekday} {hour:02d}:{minute:02d}"

    def get_teacher(self) -> str:
        """获取老师姓名"""
        return self.teacher_edit.text().strip()

    def _on_accept(self):
        """确定按钮点击"""
        self.accept()


class ClassSelectorWidget(QWidget):
    """班级选择器"""

    # 班级改变信号，传递班级ID
    class_changed = pyqtSignal(str)
    # 老师改变信号，传递老师姓名
    teacher_changed = pyqtSignal(str)
    # 班级关联的系列索引信号
    class_series_changed = pyqtSignal(int)

    @staticmethod
    def parse_class_name(class_name: str) -> dict:
        """
        解析班级名称，返回星期和时间

        Args:
            class_name: 如 "星期三 18:30"

        Returns:
            {"weekday": 3, "hour": 18, "minute": 30} 或 None
        """
        import re

        # 星期映射
        weekday_map = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "日": 7}

        # 正则匹配 "星期X HH:MM"
        match = re.match(r"星期([一二三四五六日])\s+(\d{1,2}):(\d{2})", class_name)
        if match:
            weekday_char = match.group(1)
            hour = int(match.group(2))
            minute = int(match.group(3))
            return {"weekday": weekday_map.get(weekday_char, 1), "hour": hour, "minute": minute}
        return None

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self._init_ui()
        self._load_classes()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        title_label = QLabel("班级选择")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)

        # 提示
        hint_label = QLabel("选择班级后可管理该班级的学员")
        hint_label.setStyleSheet("color: #666; font-size: 11px;")
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)

        # 班级选择行
        select_layout = QHBoxLayout()

        self.class_combo = QComboBox()
        self.class_combo.setMinimumWidth(200)
        self.class_combo.currentIndexChanged.connect(self._on_class_changed)
        select_layout.addWidget(self.class_combo, 1)

        # 添加按钮
        self.add_btn = QPushButton("添加班级")
        self.add_btn.clicked.connect(self._on_add_class)
        select_layout.addWidget(self.add_btn)

        # 删除按钮
        self.remove_btn = QPushButton("删除")
        self.remove_btn.clicked.connect(self._on_remove_class)
        select_layout.addWidget(self.remove_btn)

        layout.addLayout(select_layout)

        # 当前班级详情
        self.detail_label = QLabel()
        self.detail_label.setStyleSheet("color: #0070C0; font-size: 12px; padding: 5px;")
        layout.addWidget(self.detail_label)

        # 老师行
        teacher_layout = QHBoxLayout()
        teacher_layout.addWidget(QLabel("默认老师:"))

        self.teacher_label = QLabel()
        self.teacher_label.setStyleSheet("color: #666;")
        teacher_layout.addWidget(self.teacher_label, 1)

        self.edit_teacher_btn = QPushButton("修改")
        self.edit_teacher_btn.setMaximumWidth(60)
        self.edit_teacher_btn.clicked.connect(self._on_edit_teacher)
        teacher_layout.addWidget(self.edit_teacher_btn)

        layout.addLayout(teacher_layout)

    def _load_classes(self):
        """加载班级列表"""
        classes = self.config_manager.get_classes()
        current_id = self.config_manager._settings.get("current_class_id", "")

        self.class_combo.blockSignals(True)
        self.class_combo.clear()

        # 添加占位项
        self.class_combo.addItem("-- 请选择班级 --", "")

        current_index = 0
        for i, cls in enumerate(classes):
            class_id = cls.get("id", "")
            class_name = cls.get("name", "")
            teacher = cls.get("teacher", "")
            # 显示格式：星期x xx:xx 老师姓名
            display_text = f"{class_name} {teacher}" if teacher else class_name
            self.class_combo.addItem(display_text, class_id)

            if class_id == current_id:
                current_index = i + 1  # +1 因为有占位项

        self.class_combo.setCurrentIndex(current_index)
        self.class_combo.blockSignals(False)

        # 更新详情
        self._update_detail()

    def _update_detail(self):
        """更新详情显示"""
        current = self.config_manager.get_current_class()
        if current:
            name = current.get("name", "")
            teacher = current.get("teacher", "")
            self.detail_label.setText(f"当前班级: {name}")
            if teacher:
                self.teacher_label.setText(teacher)
            else:
                self.teacher_label.setText("(未设置)")
            self.edit_teacher_btn.setEnabled(True)
        else:
            self.detail_label.setText("当前班级: 未选择")
            self.teacher_label.setText("")
            self.edit_teacher_btn.setEnabled(False)

    def _on_class_changed(self, index):
        """班级选择改变"""
        class_id = self.class_combo.currentData()
        if class_id:
            self.config_manager.set_current_class(class_id)
            self._update_detail()
            self.class_changed.emit(class_id)
            # 发送老师信号
            current = self.config_manager.get_current_class()
            teacher = current.get("teacher", "")
            self.teacher_changed.emit(teacher)
            # 发送班级关联的系列索引
            series_index = self.config_manager.get_class_series_index(class_id)
            self.class_series_changed.emit(series_index)
        else:
            self.detail_label.setText("当前班级: 未选择")
            self.teacher_label.setText("")
            self.edit_teacher_btn.setEnabled(False)
            self.class_changed.emit("")
            self.teacher_changed.emit("")
            self.class_series_changed.emit(0)

    def _on_edit_teacher(self):
        """编辑班级老师"""
        class_id = self.class_combo.currentData()
        if not class_id:
            return

        current = self.config_manager.get_current_class()
        current_teacher = current.get("teacher", "")

        new_teacher, ok = QInputDialog.getText(
            self, "修改默认老师",
            "请输入默认授课老师:",
            QLineEdit.Normal,
            current_teacher
        )

        if ok:
            new_teacher = new_teacher.strip()
            if self.config_manager.update_class_teacher(class_id, new_teacher):
                self._update_detail()
                self.teacher_changed.emit(new_teacher)
                QMessageBox.information(self, "成功", "已更新默认老师")

    def _on_add_class(self):
        """添加新班级"""
        dialog = AddClassDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            name = dialog.get_class_name()
            teacher = dialog.get_teacher()

            class_id = self.config_manager.add_class(name, teacher)
            if class_id:
                self._load_classes()
                # 选中新添加的班级
                for i in range(self.class_combo.count()):
                    if self.class_combo.itemData(i) == class_id:
                        self.class_combo.setCurrentIndex(i)
                        break
                QMessageBox.information(self, "成功", f"已添加: {name}")
            else:
                QMessageBox.warning(self, "提示", "该班级已存在")

    def _on_remove_class(self):
        """删除当前班级"""
        class_id = self.class_combo.currentData()
        if not class_id:
            QMessageBox.warning(self, "提示", "请先选择一个班级")
            return

        class_name = self.class_combo.currentText()

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除 \"{class_name}\" 吗？\n该班级的学员数据也将被删除。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.config_manager.remove_class(class_id)
            self._load_classes()
            QMessageBox.information(self, "成功", "已删除")

    def get_current_class_id(self) -> str:
        """获取当前选择的班级ID"""
        return self.class_combo.currentData() or ""

    def refresh_class_list(self):
        """刷新班级列表（供外部调用）"""
        self._load_classes()
