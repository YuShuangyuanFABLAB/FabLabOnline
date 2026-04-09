# -*- coding: utf-8 -*-
"""
富文本编辑器组件 (F016)
支持重点/难点标记
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QToolBar, QTextEdit,
    QAction, QColorDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import (
    QTextCharFormat, QColor, QFont, QKeySequence
)
from src.ui.theme.theme_manager import ThemeManager


class RichTextEditor(QWidget):
    """富文本编辑器组件"""

    text_changed = pyqtSignal(str)

    # 预设颜色
    HIGHLIGHT_COLOR = QColor(0x00, 0x70, 0xC0)  # 重点-蓝色
    DIFFICULTY_COLOR = QColor(0xED, 0x7D, 0x31)  # 难点-橙色

    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self._placeholder = placeholder
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # 工具栏
        toolbar = QToolBar()
        toolbar.setObjectName("richTextToolBar")
        toolbar.setIconSize(toolbar.iconSize())
        toolbar.setMovable(False)

        # 重点标记
        highlight_action = QAction("重点", self)
        highlight_action.setToolTip("将选中文本标记为重点（蓝色）")
        highlight_action.setShortcut(QKeySequence("Ctrl+B"))
        highlight_action.triggered.connect(self._mark_highlight)
        toolbar.addAction(highlight_action)

        # 难点标记
        difficulty_action = QAction("难点", self)
        difficulty_action.setToolTip("将选中文本标记为难点（橙色）")
        difficulty_action.setShortcut(QKeySequence("Ctrl+D"))
        difficulty_action.triggered.connect(self._mark_difficulty)
        toolbar.addAction(difficulty_action)

        toolbar.addSeparator()

        # 清除格式
        clear_action = QAction("清除", self)
        clear_action.setToolTip("清除选中文本的格式")
        clear_action.setShortcut(QKeySequence("Ctrl+R"))
        clear_action.triggered.connect(self._clear_format)
        toolbar.addAction(clear_action)

        toolbar.addSeparator()

        # 自定义颜色
        color_action = QAction("颜色", self)
        color_action.setToolTip("自定义文字颜色")
        color_action.triggered.connect(self._custom_color)
        toolbar.addAction(color_action)

        layout.addWidget(toolbar)

        # 文本编辑区
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText(self._placeholder)
        self.text_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.text_edit)

    def _on_text_changed(self):
        """文本改变时"""
        self.text_changed.emit(self.text_edit.toHtml())

    def _mark_highlight(self):
        """标记为重点（蓝色）"""
        self._set_text_color(self.HIGHLIGHT_COLOR)

    def _mark_difficulty(self):
        """标记为难点（橙色）"""
        self._set_text_color(self.DIFFICULTY_COLOR)

    def _set_text_color(self, color: QColor):
        """设置选中文字的颜色"""
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            format = QTextCharFormat()
            format.setForeground(color)
            cursor.mergeCharFormat(format)

    def _clear_format(self):
        """清除选中文字的格式"""
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            # 获取当前主题的默认文本颜色
            colors = ThemeManager.instance().get_colors()
            default_color = QColor(colors.text_primary)

            format = QTextCharFormat()
            format.setForeground(default_color)
            format.setFontWeight(QFont.Normal)
            format.setFontItalic(False)
            format.setFontUnderline(False)
            cursor.mergeCharFormat(format)

    def _custom_color(self):
        """自定义颜色"""
        color = QColorDialog.getColor(Qt.black, self, "选择颜色")
        if color.isValid():
            self._set_text_color(color)

    def get_text(self) -> str:
        """获取纯文本"""
        return self.text_edit.toPlainText()

    def get_html(self) -> str:
        """获取HTML格式文本"""
        return self.text_edit.toHtml()

    def set_text(self, text: str):
        """设置文本"""
        self.text_edit.setPlainText(text)

    def set_html(self, html: str):
        """设置HTML文本"""
        self.text_edit.setHtml(html)

    def clear(self):
        """清空"""
        self.text_edit.clear()

    def setPlaceholderText(self, text: str):
        """设置占位文本"""
        self.text_edit.setPlaceholderText(text)
