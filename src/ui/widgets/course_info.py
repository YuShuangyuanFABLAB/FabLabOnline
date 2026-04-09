# -*- coding: utf-8 -*-
"""
课程信息输入组件 (F015)
包含基本信息输入、日期选择、课时数等
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QLineEdit, QDateTimeEdit, QCompleter,
    QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from src.ui.widgets.arrow_spinbox import ArrowSpinBox


class AutoCompleteEdit(QLineEdit):
    """带自动补全的输入框"""

    def __init__(self, items=None, parent=None):
        super().__init__(parent)
        self._model = QStandardItemModel()
        self._completer = QCompleter()
        self._completer.setModel(self._model)
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchContains)
        self.setCompleter(self._completer)

        if items:
            self.set_items(items)

    def set_items(self, items: list):
        """设置补全列表"""
        self._model.clear()
        for item in items:
            self._model.appendRow(QStandardItem(item))

    def add_item(self, item: str):
        """添加单个项目"""
        self._model.appendRow(QStandardItem(item))


class CourseInfoWidget(QWidget):
    """课程信息输入组件"""

    # 信号：数据改变
    data_changed = pyqtSignal()

    def __init__(self, recent_students=None, recent_teachers=None, parent=None):
        super().__init__(parent)
        self._recent_students = recent_students or []
        self._recent_teachers = recent_teachers or []
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 基本信息组
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)

        # 课时编号
        self.lesson_number = ArrowSpinBox()
        self.lesson_number.setRange(1, 999)
        self.lesson_number.setValue(1)
        self.lesson_number.setMinimumWidth(100)
        basic_layout.addRow("课时编号:", self.lesson_number)

        # 课程内容
        self.course_content = QLineEdit()
        self.course_content.setPlaceholderText("请输入课程内容...")
        basic_layout.addRow("课程内容:", self.course_content)

        # 学生姓名（带补全）
        self.student_name = AutoCompleteEdit(self._recent_students)
        self.student_name.setPlaceholderText("请输入学生姓名...")
        basic_layout.addRow("学生姓名:", self.student_name)

        # 授课教师（带补全）
        self.teacher_name = AutoCompleteEdit(self._recent_teachers)
        self.teacher_name.setPlaceholderText("请输入授课教师...")
        basic_layout.addRow("授课教师:", self.teacher_name)

        # 课时数
        self.class_hours = ArrowSpinBox()
        self.class_hours.setRange(1, 10)
        self.class_hours.setValue(2)
        basic_layout.addRow("课时数:", self.class_hours)

        layout.addWidget(basic_group)

        # 时间信息组
        time_group = QGroupBox("上课时间")
        time_layout = QFormLayout(time_group)

        # 上课日期时间
        self.class_date = QDateTimeEdit()
        self.class_date.setCalendarPopup(True)
        self.class_date.setDisplayFormat("yyyy年MM月dd日 HH:mm")
        self.class_date.setDateTime(QDateTime.currentDateTime())
        time_layout.addRow("上课日期:", self.class_date)

        # 结束时间
        self.class_end_time = QDateTimeEdit()
        self.class_end_time.setDisplayFormat("HH:mm")
        # 默认2小时后
        end_dt = QDateTime.currentDateTime().addSecs(2 * 3600)
        self.class_end_time.setDateTime(end_dt)
        time_layout.addRow("结束时间:", self.class_end_time)

        layout.addWidget(time_group)

        # 连接信号
        self._connect_signals()

    def _connect_signals(self):
        """连接信号"""
        self.lesson_number.valueChanged.connect(self.data_changed.emit)
        self.course_content.textChanged.connect(self.data_changed.emit)
        self.student_name.textChanged.connect(self.data_changed.emit)
        self.teacher_name.textChanged.connect(self.data_changed.emit)
        self.class_hours.valueChanged.connect(self.data_changed.emit)
        self.class_date.dateTimeChanged.connect(self.data_changed.emit)
        self.class_end_time.dateTimeChanged.connect(self.data_changed.emit)

    def get_data(self) -> dict:
        """获取输入数据"""
        start_dt = self.class_date.dateTime()
        end_dt = self.class_end_time.dateTime()

        # 格式化日期时间
        date_str = f"{start_dt.toString('yyyy年MM月dd日')} {start_dt.toString('HH:mm')}-{end_dt.toString('HH:mm')}"

        return {
            "lesson_number": self.lesson_number.value(),
            "course_content": self.course_content.text(),
            "student_name": self.student_name.text(),
            "teacher_name": self.teacher_name.text(),
            "class_hours": self.class_hours.value(),
            "class_date": date_str,
        }

    def set_data(self, data: dict):
        """设置数据"""
        if "lesson_number" in data:
            self.lesson_number.setValue(data["lesson_number"])
        if "course_content" in data:
            self.course_content.setText(data["course_content"])
        if "student_name" in data:
            self.student_name.setText(data["student_name"])
        if "teacher_name" in data:
            self.teacher_name.setText(data["teacher_name"])
        if "class_hours" in data:
            self.class_hours.setValue(data["class_hours"])
        if "class_date" in data:
            # TODO: 解析日期字符串
            pass

    def set_recent_students(self, students: list):
        """设置最近使用的学生列表"""
        self._recent_students = students
        self.student_name.set_items(students)

    def set_recent_teachers(self, teachers: list):
        """设置最近使用的教师列表"""
        self._recent_teachers = teachers
        self.teacher_name.set_items(teachers)

    def set_class_time(self, weekday: int, hour: int, minute: int):
        """
        根据班级时间设置上课日期和结束时间

        Args:
            weekday: 星期几 (1=周一, 7=周日)
            hour: 开始小时
            minute: 开始分钟
        """
        from PyQt5.QtCore import QTime

        # 获取当前日期
        now = QDateTime.currentDateTime()
        current_weekday = now.date().dayOfWeek()  # 1=周一, 7=周日

        # 计算日期偏移
        # 如果当前星期几不等于目标星期几，向前查找7天内最近的日期
        if current_weekday != weekday:
            # 计算需要往前走多少天
            diff = current_weekday - weekday
            if diff < 0:
                diff += 7
            target_date = now.addDays(-diff).date()
        else:
            target_date = now.date()

        # 设置上课日期时间
        class_datetime = QDateTime(target_date, QTime(hour, minute, 0))
        self.class_date.setDateTime(class_datetime)

        # 设置结束时间（2小时后）
        end_datetime = class_datetime.addSecs(2 * 3600)
        self.class_end_time.setDateTime(end_datetime)

    def clear(self):
        """清空输入"""
        self.lesson_number.setValue(1)
        self.course_content.clear()
        self.student_name.clear()
        self.teacher_name.clear()
        self.class_hours.setValue(2)
        self.class_date.setDateTime(QDateTime.currentDateTime())
        self.class_end_time.setDateTime(QDateTime.currentDateTime().addSecs(2 * 3600))

    def set_lesson_number(self, value: int):
        """
        设置课时编号

        Args:
            value: 课时编号值
        """
        self.lesson_number.setValue(value)
