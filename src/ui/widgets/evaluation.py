# -*- coding: utf-8 -*-
"""
评价选择组件 (F017)
12项评价、总体评价、上次作业情况
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QRadioButton, QButtonGroup, QLabel,
    QTextEdit, QScrollArea, QFrame, QPushButton
)
from PyQt5.QtCore import pyqtSignal


class EvaluationItem(QWidget):
    """单个评价项组件"""

    value_changed = pyqtSignal(str)

    def __init__(self, label: str, options: list, parent=None):
        super().__init__(parent)
        self._options = options
        self._init_ui(label, options)

    def _init_ui(self, label: str, options: list):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)  # 添加组件间距，防止文字被截断

        # 标签
        label_widget = QLabel(label)
        label_widget.setMinimumWidth(80)
        layout.addWidget(label_widget)

        # 单选按钮组
        self.button_group = QButtonGroup(self)
        self.radio_buttons = {}

        for i, opt in enumerate(options):
            rb = QRadioButton(opt)
            self.button_group.addButton(rb, i)
            self.radio_buttons[opt] = rb
            rb.toggled.connect(lambda checked, o=opt: self._on_toggled(checked, o))
            layout.addWidget(rb)

        layout.addStretch()

    def _on_toggled(self, checked: bool, option: str):
        if checked:
            self.value_changed.emit(option)

    def get_value(self) -> str:
        """获取当前选中的值"""
        for opt, rb in self.radio_buttons.items():
            if rb.isChecked():
                return opt
        return ""

    def set_value(self, value: str):
        """设置选中值"""
        if value in self.radio_buttons:
            self.radio_buttons[value].setChecked(True)

    def clear(self):
        """清除选择"""
        self.button_group.setExclusive(False)
        for rb in self.radio_buttons.values():
            rb.setChecked(False)
        self.button_group.setExclusive(True)


class EvaluationWidget(QWidget):
    """评价选择组件"""

    data_changed = pyqtSignal()
    sync_comments_requested = pyqtSignal()  # 强制同步补充说明信号

    # 12项评价名称（按PPT模板中的顺序排列：先左列从上到下，再右列从上到下）
    EVALUATION_ITEMS = [
        # 左列（从上到下）
        ("专注度与效率", "focus_efficiency"),        # 0
        ("课堂听课习惯", "listening_habit"),         # 1
        ("课堂任务完成", "task_completion"),         # 2
        ("课堂内容理解", "content_understanding"),   # 3
        ("知识熟练程度", "knowledge_proficiency"),   # 4
        ("学习方法习惯", "learning_method"),         # 5
        # 右列（从上到下）
        ("动手实践能力", "hands_on_ability"),       # 6
        ("逻辑思维表现", "logic_thinking"),          # 7
        ("想象力与创新", "imagination_creativity"),  # 8
        ("独立分析思考", "independent_analysis"),    # 9
        ("解决问题表现", "problem_solving"),         # 10
        ("挫折困难应对", "frustration_handling"),     # 11
    ]

    # 评价选项
    EVALUATION_OPTIONS = ["优", "良", "中", "差", "未体现"]

    # 总体评价选项
    OVERALL_OPTIONS = ["优", "良", "仍需努力", "需要改进"]

    # 上次作业选项
    HOMEWORK_OPTIONS = ["优", "良", "中", "差", "无"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # 课堂评价组
        eval_group = QGroupBox("课堂评价")
        eval_layout = QVBoxLayout(eval_group)

        # 12项评价
        self.evaluation_items = {}
        for label, key in self.EVALUATION_ITEMS:
            item = EvaluationItem(label, self.EVALUATION_OPTIONS)
            item.value_changed.connect(self.data_changed.emit)
            eval_layout.addWidget(item)
            self.evaluation_items[key] = item

        # 设置默认值：12项评价默认为"优"
        for item in self.evaluation_items.values():
            item.set_value("优")

        scroll_layout.addWidget(eval_group)

        # 总体评价组
        overall_group = QGroupBox("总体评价")
        overall_layout = QVBoxLayout(overall_group)
        self.overall_eval = EvaluationItem("总体表现", self.OVERALL_OPTIONS)
        self.overall_eval.value_changed.connect(self.data_changed.emit)
        overall_layout.addWidget(self.overall_eval)
        # 设置默认值：总体评价默认为"优"
        self.overall_eval.set_value("优")
        scroll_layout.addWidget(overall_group)

        # 上次作业情况组
        homework_group = QGroupBox("上次作业情况")
        homework_layout = QVBoxLayout(homework_group)
        self.homework_eval = EvaluationItem("作业评价", self.HOMEWORK_OPTIONS)
        self.homework_eval.value_changed.connect(self.data_changed.emit)
        homework_layout.addWidget(self.homework_eval)
        # 设置默认值：上次作业默认为"无"
        self.homework_eval.set_value("无")
        scroll_layout.addWidget(homework_group)

        # 补充说明组
        comments_group = QGroupBox("补充说明")
        comments_layout = QVBoxLayout(comments_group)

        self.additional_comments = QTextEdit()
        self.additional_comments.setPlaceholderText("请输入补充说明...")
        self.additional_comments.setMaximumHeight(80)
        self.additional_comments.textChanged.connect(self.data_changed.emit)
        comments_layout.addWidget(self.additional_comments)

        # 强制同步按钮
        self.sync_comments_btn = QPushButton("强制同步给所有同学")
        self.sync_comments_btn.setToolTip("将当前补充说明同步给班级所有其他同学（自动替换名字）")
        self.sync_comments_btn.clicked.connect(self._on_sync_comments)
        comments_layout.addWidget(self.sync_comments_btn)

        scroll_layout.addWidget(comments_group)

        # 课堂作业组
        homework_input_group = QGroupBox("课堂作业")
        homework_input_layout = QVBoxLayout(homework_input_group)

        self.homework = QTextEdit()
        self.homework.setPlaceholderText("请输入课堂作业...")
        self.homework.setMaximumHeight(60)
        self.homework.setPlainText("本次课无课堂作业")
        self.homework.textChanged.connect(self.data_changed.emit)
        homework_input_layout.addWidget(self.homework)

        scroll_layout.addWidget(homework_input_group)

        # 注意事项组
        notes_group = QGroupBox("注意事项")
        notes_layout = QVBoxLayout(notes_group)

        self.other_notes = QTextEdit()
        self.other_notes.setPlaceholderText("请输入注意事项...")
        self.other_notes.setMaximumHeight(60)
        self.other_notes.textChanged.connect(self.data_changed.emit)
        notes_layout.addWidget(self.other_notes)

        scroll_layout.addWidget(notes_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def get_data(self) -> dict:
        """获取所有评价数据"""
        data = {}

        # 12项评价
        for key, item in self.evaluation_items.items():
            data[key] = item.get_value()

        # 总体评价
        data["overall_evaluation"] = self.overall_eval.get_value()

        # 上次作业
        data["last_homework_status"] = self.homework_eval.get_value()

        # 文本
        data["additional_comments"] = self.additional_comments.toPlainText()
        data["homework"] = self.homework.toPlainText()
        data["other_notes"] = self.other_notes.toPlainText()

        return data

    def set_data(self, data: dict):
        """设置评价数据"""
        # 12项评价
        for key, item in self.evaluation_items.items():
            if key in data and data[key]:
                item.set_value(data[key])

        # 总体评价
        if "overall_evaluation" in data:
            self.overall_eval.set_value(data["overall_evaluation"])

        # 上次作业
        if "last_homework_status" in data:
            self.homework_eval.set_value(data["last_homework_status"])

        # 文本
        if "additional_comments" in data:
            self.additional_comments.setPlainText(data["additional_comments"])
        if "homework" in data:
            self.homework.setPlainText(data["homework"])
        if "other_notes" in data:
            self.other_notes.setPlainText(data["other_notes"])

    def clear(self):
        """清空所有"""
        for item in self.evaluation_items.values():
            item.clear()
        self.overall_eval.clear()
        self.homework_eval.clear()
        self.additional_comments.clear()
        self.homework.clear()
        self.other_notes.clear()

    def _on_sync_comments(self):
        """强制同步按钮点击"""
        self.sync_comments_requested.emit()
