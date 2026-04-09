# -*- coding: utf-8 -*-
"""
带三角形箭头的 SpinBox
"""

from PyQt5.QtWidgets import QSpinBox, QStyle, QStyleOptionSpinBox
from PyQt5.QtGui import QPainter, QBrush, QColor
from PyQt5.QtCore import Qt, QPoint

from src.ui.theme import ThemeManager


class ArrowSpinBox(QSpinBox):
    """带三角形箭头的 SpinBox"""

    def paintEvent(self, event):
        """重写绘制事件，在按钮区域绘制三角形箭头"""
        super().paintEvent(event)

        # 获取主题颜色
        colors = ThemeManager.instance().get_colors()

        # 初始化样式选项
        option = QStyleOptionSpinBox()
        self.initStyleOption(option)

        # 获取按钮区域
        up_rect = self.style().subControlRect(
            QStyle.CC_SpinBox, option, QStyle.SC_SpinBoxUp, self
        )
        down_rect = self.style().subControlRect(
            QStyle.CC_SpinBox, option, QStyle.SC_SpinBoxDown, self
        )

        # 绘制箭头
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 使用主题文字颜色
        arrow_color = QColor(colors.text_secondary)

        # 绘制上箭头（三角形指向上方）
        if up_rect.isValid():
            self._draw_triangle(painter, up_rect, arrow_color, up=True)

        # 绘制下箭头（三角形指向下方）
        if down_rect.isValid():
            self._draw_triangle(painter, down_rect, arrow_color, up=False)

        painter.end()

    def _draw_triangle(self, painter, rect, color, up):
        """绘制三角形箭头"""
        painter.save()

        # 设置画笔和画刷
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(color))

        # 计算三角形顶点 - 减小 margin让三角形更大更明显
        margin_x = 3  # 水平边距
        margin_y = 2  # 垂直边距

        if up:
            # 向上箭头：顶点在上方
            top = QPoint(rect.center().x(), rect.top() + margin_y)
            left = QPoint(rect.left() + margin_x, rect.bottom() - margin_y)
            right = QPoint(rect.right() - margin_x, rect.bottom() - margin_y)
        else:
            # 向下箭头：顶点在下方
            bottom = QPoint(rect.center().x(), rect.bottom() - margin_y)
            left = QPoint(rect.left() + margin_x, rect.top() + margin_y)
            right = QPoint(rect.right() - margin_x, rect.top() + margin_y)

        # 绘制三角形
        from PyQt5.QtGui import QPolygon
        polygon = QPolygon([top if up else bottom, left, right])
        painter.drawPolygon(polygon)

        painter.restore()
