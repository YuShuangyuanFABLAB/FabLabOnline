# -*- coding: utf-8 -*-
"""
图片上传组件 (F018)
支持拖拽上传、点击选择、预览、删除
"""

import os
from pathlib import Path
from typing import List

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QFrame, QFileDialog,
    QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QDragEnterEvent, QDropEvent

from src.ui.theme import ThemeManager


class ImagePreviewWidget(QLabel):
    """图片预览组件（支持删除和裁剪）"""

    delete_clicked = pyqtSignal()  # 删除信号
    crop_clicked = pyqtSignal()  # 裁剪信号
    clicked = pyqtSignal()  # 点击信号

    def __init__(self, image_path: str = None, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self._hover = False
        self._crop_mode = False  # 是否显示裁剪按钮
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedSize(120, 120)
        self.setAlignment(Qt.AlignCenter)
        self._apply_preview_style()
        self.setCursor(Qt.PointingHandCursor)
        self.setScaledContents(False)

        # 连接主题变化信号
        ThemeManager.instance().theme_changed.connect(self._on_theme_changed)

        if self.image_path and os.path.exists(self.image_path):
            self._load_image()

    def _on_theme_changed(self, theme_name: str):
        """主题变化时更新样式"""
        self._apply_preview_style()

    def _apply_preview_style(self):
        """应用预览样式"""
        colors = ThemeManager.instance().get_colors()
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {colors.preview_background};
                border: 2px solid {colors.preview_border};
                border-radius: 5px;
            }}
            QLabel:hover {{
                border-color: {colors.preview_border_hover};
            }}
        """)

    def _load_image(self):
        """加载图片"""
        pixmap = QPixmap(self.image_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                116, 116,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.setPixmap(scaled)

    def set_image(self, image_path: str):
        """设置图片"""
        self.image_path = image_path
        self._load_image()

    def paintEvent(self, event):
        super().paintEvent(event)

        # 悬停时显示操作按钮
        if self._hover:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # 半透明遮罩
            painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

            # 删除图标（右上角X）
            painter.setPen(QPen(QColor(255, 100, 100), 3))
            # 右上角
            painter.drawLine(
                self.width() - 25, 5,
                self.width() - 5, 25
            )
            painter.drawLine(
                self.width() - 5, 5,
                self.width() - 25, 25
            )

            # 裁剪图标（中心）
            painter.setPen(QPen(QColor(100, 200, 100), 2))
            painter.drawRect(45, 45, 30, 30)
            painter.drawLine(40, 50, 50, 50)
            painter.drawLine(40, 70, 50, 70)
            painter.drawLine(70, 50, 80, 50)
            painter.drawLine(70, 70, 80, 70)

    def _get_click_area(self, pos) -> str:
        """判断点击区域"""
        x, y = pos.x(), pos.y()
        # 右上角删除区域
        if x > self.width() - 30 and y < 30:
            return "delete"
        # 中心裁剪区域
        if 40 < x < 80 and 40 < y < 80:
            return "crop"
        return "default"

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            area = self._get_click_area(event.pos())
            if area == "delete":
                self.delete_clicked.emit()
            elif area == "crop":
                self.crop_clicked.emit()
            else:
                self.clicked.emit()


class ImageUploadWidget(QWidget):
    """图片上传组件"""

    images_changed = pyqtSignal(list)  # 图片列表改变信号
    sync_toggled = pyqtSignal(bool)    # 同步状态切换信号

    def __init__(self, title: str = "图片上传", max_images: int = 10,
                 show_sync_button: bool = False, parent=None):
        super().__init__(parent)
        self._title = title
        self._max_images = max_images
        self._show_sync_button = show_sync_button
        self._sync_enabled = True  # 默认同步
        self._image_paths: List[str] = []
        self._setup_ui()
        self.setAcceptDrops(True)

        # 连接主题变化信号
        ThemeManager.instance().theme_changed.connect(self._apply_theme)
        self._apply_theme(ThemeManager.instance().get_current_theme())

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题栏
        header_layout = QHBoxLayout()
        self.title_label = QLabel(self._title)
        self.title_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self.title_label)

        # 同步按钮（可选）
        if self._show_sync_button:
            self.sync_btn = QPushButton("同步")
            self.sync_btn.setCheckable(True)
            self.sync_btn.setChecked(True)  # 默认按下
            self.sync_btn.setFixedWidth(50)
            self.sync_btn.clicked.connect(self._on_sync_toggled)
            self._update_sync_btn_style()
            header_layout.addWidget(self.sync_btn)

        self.count_label = QLabel(f"0/{self._max_images}")
        header_layout.addWidget(self.count_label)
        header_layout.addStretch()

        # 添加按钮
        add_btn = QPushButton("添加图片")
        add_btn.clicked.connect(self._on_add_images)
        header_layout.addWidget(add_btn)

        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self.clear_images)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # 图片预览区域 - 使用 QFrame 包裹实现边框
        self.border_frame = QFrame()
        self.border_frame.setObjectName("imagePreviewFrame")

        frame_layout = QVBoxLayout(self.border_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)

        # QScrollArea 设置（无边框、透明背景）
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.preview_container = QWidget()
        self.preview_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.preview_layout = QHBoxLayout(self.preview_container)
        self.preview_layout.setAlignment(Qt.AlignLeft)
        self.preview_layout.setContentsMargins(8, 8, 8, 8)
        self.preview_layout.setSpacing(5)

        # 添加占位标签
        self._placeholder = QLabel("拖拽图片到此处或点击\"添加图片\"按钮")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setStyleSheet("color: #999; font-size: 12px;")
        self.preview_layout.addWidget(self._placeholder)
        self.preview_layout.addStretch()

        self.scroll.setWidget(self.preview_container)
        frame_layout.addWidget(self.scroll)
        layout.addWidget(self.border_frame)

    def _apply_theme(self, theme_name: str):
        """应用主题"""
        colors = ThemeManager.instance().get_colors()

        # 标题标签
        self.title_label.setStyleSheet(f"""
            font-weight: bold;
            color: {colors.text_primary};
        """)

        # 计数标签
        self.count_label.setStyleSheet(f"color: {colors.text_secondary};")

        # 占位标签
        self._placeholder.setStyleSheet(f"""
            color: {colors.text_hint};
            font-size: 12px;
        """)

        # 边框样式应用在 QFrame 上
        self.border_frame.setStyleSheet(f"""
            QFrame#imagePreviewFrame {{
                background-color: {colors.scroll_area_background};
                border: 2px solid {colors.border_normal};
                border-radius: 4px;
            }}
        """)

        # QScrollArea 完全透明
        self.scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        # 同步按钮
        if self._show_sync_button:
            self._update_sync_btn_style()

    def _on_theme_changed(self, theme_name: str):
        """主题变化回调"""
        self._apply_theme(theme_name)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            # 检查是否有图片文件
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if self._is_image_file(path):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if self._is_image_file(path) and os.path.exists(path):
                files.append(path)

        if files:
            self.add_images(files)

    def _is_image_file(self, path: str) -> bool:
        """检查是否是图片文件"""
        ext = Path(path).suffix.lower()
        return ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']

    def _on_add_images(self):
        """添加图片按钮点击"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片",
            "",
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif *.webp);;所有文件 (*)"
        )

        if files:
            self.add_images(files)

    def add_images(self, paths: List[str]):
        """添加图片"""
        available = self._max_images - len(self._image_paths)
        if available <= 0:
            QMessageBox.warning(self, "提示", f"最多只能上传{self._max_images}张图片")
            return

        # 只添加可用数量
        to_add = paths[:available]
        for path in to_add:
            if path not in self._image_paths:
                self._image_paths.append(path)
                self._add_preview_widget(path)

        self._update_ui()
        self.images_changed.emit(self._image_paths)

    def _add_preview_widget(self, image_path: str):
        """添加预览组件"""
        preview = ImagePreviewWidget(image_path)
        preview.delete_clicked.connect(lambda: self._remove_image(image_path))
        preview.crop_clicked.connect(lambda: self._crop_image(image_path))
        preview.clicked.connect(lambda: self._preview_image(image_path))

        # 在stretch之前插入
        index = self.preview_layout.count() - 1  # 最后一个是stretch
        self.preview_layout.insertWidget(index, preview)

    def _remove_image(self, path: str):
        """移除图片"""
        if path in self._image_paths:
            self._image_paths.remove(path)
            self._refresh_previews()
            self._update_ui()
            self.images_changed.emit(self._image_paths)

    def _refresh_previews(self):
        """刷新预览"""
        # 清除所有预览组件（保留 _placeholder 和 stretch）
        # 布局顺序: [_placeholder, previews..., stretch]
        # 需要删除的是索引 1 到 count-2 之间的组件
        while self.preview_layout.count() > 2:
            # 删除索引 1 的组件（第一个预览组件）
            item = self.preview_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        # 重新添加预览组件
        for path in self._image_paths:
            self._add_preview_widget(path)

    def _preview_image(self, path: str):
        """预览大图"""
        # 在系统默认程序中打开
        import subprocess
        import platform

        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])

    def _crop_image(self, path: str):
        """裁剪图片"""
        from src.ui.dialogs.crop_dialog import CropDialog

        dialog = CropDialog(path, self)
        if dialog.exec_():
            # 获取裁剪后的图片
            cropped = dialog.get_cropped_image()
            if cropped:
                # 保存裁剪结果（覆盖原文件或保存为新文件）
                base = Path(path)
                new_path = str(base.parent / f"{base.stem}_cropped{base.suffix}")
                cropped.save(new_path)

                # 更新图片路径
                if path in self._image_paths:
                    idx = self._image_paths.index(path)
                    self._image_paths[idx] = new_path

                self._refresh_previews()
                self.images_changed.emit(self._image_paths)

    def _update_ui(self):
        """更新UI状态"""
        self.count_label.setText(f"{len(self._image_paths)}/{self._max_images}")

        # 显示/隐藏占位标签
        self._placeholder.setVisible(len(self._image_paths) == 0)

    def get_images(self) -> List[str]:
        """获取所有图片路径"""
        return self._image_paths.copy()

    def set_images(self, paths: List[str]):
        """设置图片"""
        self._image_paths = []
        self._refresh_previews()

        for path in paths:
            if os.path.exists(path):
                self._image_paths.append(path)
                self._add_preview_widget(path)

        self._update_ui()
        self.images_changed.emit(self._image_paths)

    def clear_images(self):
        """清空所有图片"""
        self._image_paths = []
        self._refresh_previews()
        self._update_ui()
        self.images_changed.emit([])

    def _on_sync_toggled(self, checked: bool):
        """同步按钮切换"""
        self._sync_enabled = checked
        self._update_sync_btn_style()
        self.sync_toggled.emit(checked)

    def _update_sync_btn_style(self):
        """更新同步按钮样式"""
        colors = ThemeManager.instance().get_colors()

        if self._sync_enabled:
            self.sync_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors.primary};
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 2px 6px;
                }}
                QPushButton:hover {{
                    background-color: {colors.primary_hover};
                }}
            """)
        else:
            self.sync_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors.button_normal};
                    color: {colors.text_secondary};
                    border: 1px solid {colors.border_normal};
                    border-radius: 3px;
                    padding: 2px 6px;
                }}
                QPushButton:hover {{
                    background-color: {colors.background_tertiary};
                }}
            """)

    def is_sync_enabled(self) -> bool:
        """获取同步状态"""
        return self._sync_enabled

    def set_sync_enabled(self, enabled: bool):
        """设置同步状态"""
        if self._show_sync_button:
            self._sync_enabled = enabled
            self.sync_btn.setChecked(enabled)
            self._update_sync_btn_style()
