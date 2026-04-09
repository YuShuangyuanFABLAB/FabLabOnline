# -*- coding: utf-8 -*-
"""
学员管理组件
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QDialog, QFormLayout,
    QLineEdit, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal

from src.ui.theme import ThemeManager


class AddStudentDialog(QDialog):
    """添加学员对话框"""

    def __init__(self, parent=None, student_name: str = "", nickname: str = ""):
        super().__init__(parent)
        self.setWindowTitle("添加学员")
        self.setModal(True)
        self.setMinimumWidth(300)
        self._is_edit = bool(student_name)

        if self._is_edit:
            self.setWindowTitle("编辑学员")

        self._init_ui()

        # 填充现有数据（编辑模式）
        if student_name:
            self.name_edit.setText(student_name)
        if nickname:
            self.nickname_edit.setText(nickname)

    def _init_ui(self):
        layout = QFormLayout(self)

        # 姓名输入
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入学员姓名")
        layout.addRow("姓名:", self.name_edit)

        # 昵称输入
        self.nickname_edit = QLineEdit()
        self.nickname_edit.setPlaceholderText("可选，用于显示更亲切的称呼")
        layout.addRow("昵称:", self.nickname_edit)

        # 按钮
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self._on_accept)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addRow(btn_layout)

    def _on_accept(self):
        """确定按钮点击"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入学员姓名")
            return
        self.accept()

    def get_student_info(self) -> tuple:
        """获取输入的学员信息"""
        name = self.name_edit.text().strip()
        nickname = self.nickname_edit.text().strip()
        return name, nickname


class StudentManagerWidget(QWidget):
    """学员管理器"""

    # 学员选择信号，传递学员姓名
    student_selected = pyqtSignal(str)
    # 学员列表变化信号
    students_changed = pyqtSignal()

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self._current_class_id = ""
        self._init_ui()

        # 连接主题变化信号
        ThemeManager.instance().theme_changed.connect(self._apply_theme)
        self._apply_theme(ThemeManager.instance().get_current_theme())

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        self.title_label = QLabel("学员管理")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.title_label)

        # 提示
        self.hint_label = QLabel("请先选择班级")
        self.hint_label.setStyleSheet("color: #666; font-size: 11px;")
        self.hint_label.setWordWrap(True)
        layout.addWidget(self.hint_label)

        # 学员列表
        self.student_list = QListWidget()
        self.student_list.setMinimumHeight(120)
        self.student_list.itemDoubleClicked.connect(self._on_student_double_clicked)
        layout.addWidget(self.student_list)

        # 按钮行
        btn_layout = QHBoxLayout()

        self.add_btn = QPushButton("添加学员")
        self.add_btn.clicked.connect(self._on_add_student)
        btn_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self._on_edit_student)
        btn_layout.addWidget(self.edit_btn)

        self.remove_btn = QPushButton("删除")
        self.remove_btn.clicked.connect(self._on_remove_student)
        btn_layout.addWidget(self.remove_btn)

        self.use_btn = QPushButton("使用")
        self.use_btn.setToolTip("将选中学员姓名填入表单")
        self.use_btn.clicked.connect(self._on_use_student)
        btn_layout.addWidget(self.use_btn)

        layout.addLayout(btn_layout)

    def _apply_theme(self, theme_name: str):
        """应用主题"""
        colors = ThemeManager.instance().get_colors()

        # 标题标签
        self.title_label.setStyleSheet(f"""
            font-weight: bold;
            font-size: 14px;
            color: {colors.text_primary};
        """)

        # 提示标签
        self.hint_label.setStyleSheet(f"""
            color: {colors.text_secondary};
            font-size: 11px;
        """)

    def load_students(self, class_id: str):
        """加载班级学员"""
        self._current_class_id = class_id
        self.student_list.clear()

        if not class_id:
            self.hint_label.setText("请先选择班级")
            self._update_buttons(False)
            return

        students = self.config_manager.get_students_by_class(class_id)

        if students:
            self.hint_label.setText(f"共 {len(students)} 名学员")
            for student in students:
                name = student.get("name", "")
                nickname = student.get("nickname", "")
                if nickname:
                    display_text = f"{name} ({nickname})"
                else:
                    display_text = name
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, name)  # 存储姓名
                self.student_list.addItem(item)
        else:
            self.hint_label.setText("暂无学员，点击添加")

        self._update_buttons(True)

    def _update_buttons(self, enabled: bool):
        """更新按钮状态"""
        self.add_btn.setEnabled(enabled)

    def _get_selected_index(self) -> int:
        """获取选中项的索引"""
        return self.student_list.currentRow()

    def _on_add_student(self):
        """添加学员"""
        if not self._current_class_id:
            QMessageBox.warning(self, "提示", "请先选择班级")
            return

        dialog = AddStudentDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            name, nickname = dialog.get_student_info()

            if not name:
                return

            if self.config_manager.add_student(self._current_class_id, name, nickname):
                self.load_students(self._current_class_id)
                self.students_changed.emit()
                QMessageBox.information(self, "成功", f"已添加: {name}")
            else:
                QMessageBox.warning(self, "提示", "该学员已存在")

    def _on_edit_student(self):
        """编辑学员"""
        index = self._get_selected_index()
        if index < 0:
            QMessageBox.warning(self, "提示", "请先选择学员")
            return

        students = self.config_manager.get_students_by_class(self._current_class_id)
        if index >= len(students):
            return

        student = students[index]
        old_name = student.get("name", "")
        old_nickname = student.get("nickname", "")

        dialog = AddStudentDialog(self, old_name, old_nickname)
        if dialog.exec_() == QDialog.Accepted:
            new_name, new_nickname = dialog.get_student_info()

            if not new_name:
                return

            if self.config_manager.update_student(
                self._current_class_id, index, new_name, new_nickname
            ):
                self.load_students(self._current_class_id)
                self.students_changed.emit()
                QMessageBox.information(self, "成功", "已更新")
            else:
                QMessageBox.warning(self, "提示", "更新失败")

    def _on_remove_student(self):
        """删除学员"""
        index = self._get_selected_index()
        if index < 0:
            QMessageBox.warning(self, "提示", "请先选择学员")
            return

        item = self.student_list.currentItem()
        display_text = item.text()

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除 \"{display_text}\" 吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.config_manager.remove_student(self._current_class_id, index):
                self.load_students(self._current_class_id)
                self.students_changed.emit()
                QMessageBox.information(self, "成功", "已删除")

    def _on_use_student(self):
        """使用选中的学员（填充到表单）"""
        item = self.student_list.currentItem()
        if not item:
            QMessageBox.warning(self, "提示", "请先选择学员")
            return

        name = item.data(Qt.UserRole)
        self.student_selected.emit(name)

    def _on_student_double_clicked(self, item):
        """双击学员项时使用该学员"""
        name = item.data(Qt.UserRole)
        self.student_selected.emit(name)

    def get_current_class_id(self) -> str:
        """获取当前班级ID"""
        return self._current_class_id
