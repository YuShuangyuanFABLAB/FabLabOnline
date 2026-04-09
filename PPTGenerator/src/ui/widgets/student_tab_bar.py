# -*- coding: utf-8 -*-
"""
学员选择标签栏组件
以按钮组形式显示学员，支持互斥选择
同时支持为每个学员单独选择是否生成PPT
"""

from typing import List, Dict, Tuple
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QScrollArea, QFrame,
    QButtonGroup
)
from PyQt5.QtCore import pyqtSignal, Qt

from src.ui.theme import ThemeManager


class StudentTabBar(QWidget):
    """学员选择标签栏（按钮组形式）"""

    # 学员切换信号
    student_tab_changed = pyqtSignal(str)
    # 生成选择变化信号
    generation_selection_changed = pyqtSignal(list)  # 选中的学员名列表

    def __init__(self, parent=None):
        super().__init__(parent)
        # 学员名 -> (姓名按钮, 生成按钮)
        self._buttons: Dict[str, Tuple[QPushButton, QPushButton]] = {}
        self._button_group: QButtonGroup = None  # 按钮组（互斥选择）
        self._current_student: str = ""
        self._block_signal = False  # 是否阻止信号
        self._init_ui()

        # 连接主题变化信号
        ThemeManager.instance().theme_changed.connect(self._apply_theme)
        self._apply_theme(ThemeManager.instance().get_current_theme())

    def _init_ui(self):
        """初始化UI"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # 标签
        self._title_label = QLabel("学员:")
        self._title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        main_layout.addWidget(self._title_label)

        # 滚动区域（容纳按钮）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        # 按钮容器
        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(3)
        self.button_layout.addStretch()

        scroll.setWidget(self.button_container)
        main_layout.addWidget(scroll, 1)  # 滚动区域可伸缩

        # 提示标签（无学员时显示）
        self.empty_label = QLabel("暂无学员")
        self.empty_label.setStyleSheet("color: #999; font-size: 11px;")
        self.empty_label.hide()
        main_layout.addWidget(self.empty_label)

        # 全选/取消按钮容器
        self._batch_btn_container = QWidget()
        batch_btn_layout = QHBoxLayout(self._batch_btn_container)
        batch_btn_layout.setContentsMargins(0, 0, 0, 0)
        batch_btn_layout.setSpacing(3)

        self._select_all_btn = QPushButton("全选")
        self._select_all_btn.setFixedHeight(24)
        self._select_all_btn.setCursor(Qt.PointingHandCursor)
        self._select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #e8f4e8;
                border: 1px solid #4caf50;
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 11px;
                color: #2e7d32;
            }
            QPushButton:hover {
                background-color: #c8e6c9;
            }
        """)
        self._select_all_btn.clicked.connect(self.select_all_for_generation)
        batch_btn_layout.addWidget(self._select_all_btn)

        self._deselect_all_btn = QPushButton("取消")
        self._deselect_all_btn.setFixedHeight(24)
        self._deselect_all_btn.setCursor(Qt.PointingHandCursor)
        self._deselect_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffebee;
                border: 1px solid #f44336;
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 11px;
                color: #c62828;
            }
            QPushButton:hover {
                background-color: #ffcdd2;
            }
        """)
        self._deselect_all_btn.clicked.connect(self.deselect_all_for_generation)
        batch_btn_layout.addWidget(self._deselect_all_btn)

        main_layout.addWidget(self._batch_btn_container)

        # 创建按钮组（实现互斥选择）
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)
        self._button_group.buttonClicked.connect(self._on_group_button_clicked)

    def load_students(self, students: List[Dict[str, str]]):
        """
        加载学员列表，刷新按钮

        Args:
            students: 学员列表，每项包含 name 和可选的 nickname
        """
        # 清除现有按钮
        self._clear_buttons()

        if not students:
            self.empty_label.show()
            self.button_container.hide()
            self._batch_btn_container.hide()
            self._current_student = ""
            return

        self.empty_label.hide()
        self.button_container.show()
        self._batch_btn_container.show()

        # 创建按钮
        for student in students:
            name = student.get("name", "")
            nickname = student.get("nickname", "")

            if not name:
                continue

            # 显示文本
            if nickname:
                display_text = f"{name}({nickname})"
            else:
                display_text = name

            # 创建姓名按钮
            name_btn = QPushButton(display_text)
            name_btn.setCheckable(True)
            name_btn.setCursor(Qt.PointingHandCursor)
            name_btn.setMinimumHeight(28)

            # 姓名按钮样式
            self._update_name_btn_style(name_btn, False)

            # 创建生成按钮（独立的开关按钮）
            gen_btn = QPushButton("✓")
            gen_btn.setCheckable(True)
            gen_btn.setChecked(False)  # 默认不生成
            gen_btn.setCursor(Qt.PointingHandCursor)
            gen_btn.setFixedSize(32, 32)
            gen_btn.setToolTip("点击选择是否生成此学员的PPT")
            gen_btn.clicked.connect(lambda checked, n=name: self._on_gen_btn_clicked(n, checked))

            # 生成按钮样式
            self._update_gen_btn_style(gen_btn, False)

            # 添加姓名按钮到按钮组（自动实现互斥）
            self._button_group.addButton(name_btn)

            # 插入到 stretch 之前
            insert_idx = self.button_layout.count() - 1
            self.button_layout.insertWidget(insert_idx, name_btn)
            self.button_layout.insertWidget(insert_idx + 1, gen_btn)

            self._buttons[name] = (name_btn, gen_btn)

    def _update_gen_btn_style(self, btn: QPushButton, checked: bool):
        """更新生成按钮样式"""
        colors = ThemeManager.instance().get_colors()

        if checked:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors.success};
                    border: 2px solid {colors.success};
                    border-radius: 3px;
                    color: white;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    background-color: {colors.success_hover};
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors.button_normal};
                    border: 2px solid {colors.border_normal};
                    border-radius: 3px;
                    color: {colors.text_hint};
                    font-size: 14px;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    background-color: {colors.background_tertiary};
                    color: {colors.text_secondary};
                }}
            """)

    def _on_gen_btn_clicked(self, name: str, checked: bool):
        """生成按钮点击事件"""
        if name in self._buttons:
            _, gen_btn = self._buttons[name]
            self._update_gen_btn_style(gen_btn, checked)
            # 发射选择变化信号
            self.generation_selection_changed.emit(self.get_selected_for_generation())

    def _clear_buttons(self):
        """清除所有按钮"""
        # 从按钮组中移除所有按钮
        for name_btn, gen_btn in self._buttons.values():
            self._button_group.removeButton(name_btn)
            name_btn.deleteLater()
            gen_btn.deleteLater()
        self._buttons.clear()
        self._current_student = ""

    def _on_group_button_clicked(self, btn: QPushButton):
        """按钮组点击事件（QButtonGroup 自动处理互斥）"""
        # 找到对应的学员名
        student_name = None
        for name, (name_btn, gen_btn) in self._buttons.items():
            if name_btn is btn:
                student_name = name
                break

        if not student_name:
            return

        self._current_student = student_name

        # 更新所有按钮的样式
        for n, (name_btn, gen_btn) in self._buttons.items():
            self._update_name_btn_style(name_btn, name_btn.isChecked())

        # 发射信号
        if not self._block_signal:
            self.student_tab_changed.emit(student_name)

    def set_current_student(self, student_name: str):
        """
        设置当前学员（不触发信号）

        Args:
            student_name: 学员姓名
        """
        if student_name not in self._buttons:
            return

        # 阻止信号
        self._block_signal = True

        # 使用按钮组的方式设置选中（自动取消其他按钮）
        name_btn, _ = self._buttons[student_name]
        name_btn.setChecked(True)
        self._current_student = student_name

        # 更新所有按钮的样式
        for n, (name_btn, gen_btn) in self._buttons.items():
            self._update_name_btn_style(name_btn, name_btn.isChecked())

        # 恢复信号
        self._block_signal = False

    def get_current_student(self) -> str:
        """获取当前选中学员"""
        return self._current_student

    def clear_selection(self):
        """清除选择"""
        self._block_signal = True
        # 临时禁用互斥以清除所有选中
        self._button_group.setExclusive(False)
        for name_btn, gen_btn in self._buttons.values():
            name_btn.setChecked(False)
        self._button_group.setExclusive(True)
        self._current_student = ""
        self._block_signal = False

    def add_student(self, name: str, nickname: str = ""):
        """
        添加单个学员按钮

        Args:
            name: 学员姓名
            nickname: 昵称（可选）
        """
        if name in self._buttons:
            return

        # 显示文本
        if nickname:
            display_text = f"{name}({nickname})"
        else:
            display_text = name

        # 创建姓名按钮
        name_btn = QPushButton(display_text)
        name_btn.setCheckable(True)
        name_btn.setCursor(Qt.PointingHandCursor)
        name_btn.setMinimumHeight(28)

        # 姓名按钮样式
        self._update_name_btn_style(name_btn, False)

        # 创建生成按钮
        gen_btn = QPushButton("✓")
        gen_btn.setCheckable(True)
        gen_btn.setChecked(False)
        gen_btn.setCursor(Qt.PointingHandCursor)
        gen_btn.setFixedSize(28, 28)
        gen_btn.setToolTip("点击选择是否生成此学员的PPT")
        gen_btn.clicked.connect(lambda checked, n=name: self._on_gen_btn_clicked(n, checked))
        self._update_gen_btn_style(gen_btn, False)

        # 添加到按钮组
        self._button_group.addButton(name_btn)

        # 隐藏空提示
        self.empty_label.hide()
        self.button_container.show()
        self._batch_btn_container.show()

        # 插入按钮
        insert_idx = self.button_layout.count() - 1
        self.button_layout.insertWidget(insert_idx, name_btn)
        self.button_layout.insertWidget(insert_idx + 1, gen_btn)
        self._buttons[name] = (name_btn, gen_btn)

    def remove_student(self, name: str):
        """
        移除学员按钮

        Args:
            name: 学员姓名
        """
        if name not in self._buttons:
            return

        name_btn, gen_btn = self._buttons.pop(name)
        self._button_group.removeButton(name_btn)
        name_btn.deleteLater()
        gen_btn.deleteLater()

        if name == self._current_student:
            self._current_student = ""

        # 如果没有学员了，显示空提示
        if not self._buttons:
            self.empty_label.show()
            self.button_container.hide()
            self._batch_btn_container.hide()

    def update_student(self, old_name: str, new_name: str, nickname: str = ""):
        """
        更新学员信息

        Args:
            old_name: 原姓名
            new_name: 新姓名
            nickname: 昵称（可选）
        """
        if old_name not in self._buttons:
            return

        name_btn, gen_btn = self._buttons.pop(old_name)

        # 显示文本
        if nickname:
            display_text = f"{new_name}({nickname})"
        else:
            display_text = new_name

        name_btn.setText(display_text)

        self._buttons[new_name] = (name_btn, gen_btn)

        # 更新当前学员
        if self._current_student == old_name:
            self._current_student = new_name

    # ==================== 生成选择相关方法 ====================

    def get_selected_for_generation(self) -> List[str]:
        """
        获取被选中生成的学员名列表

        Returns:
            选中生成的学员名列表
        """
        selected = []
        for name, (name_btn, gen_btn) in self._buttons.items():
            if gen_btn.isChecked():
                selected.append(name)
        return selected

    def select_all_for_generation(self):
        """全选所有学员用于生成"""
        for name_btn, gen_btn in self._buttons.values():
            gen_btn.setChecked(True)
            self._update_gen_btn_style(gen_btn, True)
        # 发射信号
        self.generation_selection_changed.emit(self.get_selected_for_generation())

    def deselect_all_for_generation(self):
        """取消所有学员的生成选择"""
        for name_btn, gen_btn in self._buttons.values():
            gen_btn.setChecked(False)
            self._update_gen_btn_style(gen_btn, False)
        # 发射信号
        self.generation_selection_changed.emit([])

    def get_generation_count(self) -> int:
        """
        获取选中生成的学员数量

        Returns:
            选中数量
        """
        return len(self.get_selected_for_generation())

    def set_student_generation(self, name: str, selected: bool):
        """
        设置单个学员的生成选择状态

        Args:
            name: 学员姓名
            selected: 是否选中生成
        """
        if name in self._buttons:
            _, gen_btn = self._buttons[name]
            gen_btn.setChecked(selected)
            self._update_gen_btn_style(gen_btn, selected)
            self.generation_selection_changed.emit(self.get_selected_for_generation())

    # ==================== 主题支持 ====================

    def _apply_theme(self, theme_name: str):
        """应用主题"""
        colors = ThemeManager.instance().get_colors()

        # 标题标签
        self._title_label.setStyleSheet(f"""
            font-weight: bold;
            font-size: 12px;
            color: {colors.text_primary};
        """)

        # 空提示标签
        self.empty_label.setStyleSheet(f"""
            color: {colors.text_hint};
            font-size: 11px;
        """)

        # 全选按钮
        self._select_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.success_background};
                border: 1px solid {colors.success_border};
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 11px;
                color: {colors.success_text};
            }}
            QPushButton:hover {{
                background-color: {colors.success_hover};
            }}
        """)

        # 取消按钮
        self._deselect_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.error_background};
                border: 1px solid {colors.error_border};
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 11px;
                color: {colors.error_text};
            }}
            QPushButton:hover {{
                background-color: {colors.error_hover};
            }}
        """)

        # 更新所有学员按钮
        for name, (name_btn, gen_btn) in self._buttons.items():
            self._update_name_btn_style(name_btn, name_btn.isChecked())
            self._update_gen_btn_style(gen_btn, gen_btn.isChecked())

    def _update_name_btn_style(self, btn: QPushButton, checked: bool):
        """更新姓名按钮样式"""
        colors = ThemeManager.instance().get_colors()

        if checked:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors.primary};
                    border: 1px solid {colors.primary};
                    border-radius: 3px;
                    padding: 4px 12px;
                    font-size: 12px;
                    color: white;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors.button_normal};
                    border: 1px solid {colors.border_normal};
                    border-radius: 3px;
                    padding: 4px 12px;
                    font-size: 12px;
                    color: {colors.text_primary};
                }}
                QPushButton:hover {{
                    background-color: {colors.background_tertiary};
                    border-color: {colors.border_hover};
                }}
            """)
