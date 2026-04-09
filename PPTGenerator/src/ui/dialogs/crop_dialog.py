# -*- coding: utf-8 -*-
"""
图片裁剪对话框 (F019)
支持手动裁剪、旋转功能
"""

from typing import Optional
from pathlib import Path

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QMessageBox,
    QFileDialog, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QBrush

from PIL import Image

from src.ui.widgets.arrow_spinbox import ArrowSpinBox


class CropDialog(QDialog):
    """图片裁剪对话框"""

    def __init__(self, image_path: str = None, parent=None):
        super().__init__(parent)
        self._image_path = image_path
        self._original_image: Optional[Image.Image] = None
        self._current_image: Optional[Image.Image] = None
        self._rotation = 0
        self._crop_rect = None
        self._init_ui()

        if image_path and Path(image_path).exists():
            self._load_image(image_path)

    def _init_ui(self):
        self.setWindowTitle("图片裁剪")
        self.setMinimumSize(800, 600)

        layout = QHBoxLayout(self)

        # 左侧：预览区域
        left_layout = QVBoxLayout()

        # 图片预览
        self.preview_label = QLabel("请选择图片")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(500, 400)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                border: 2px solid #555;
                border-radius: 5px;
                color: #888;
                font-size: 14px;
            }
        """)
        left_layout.addWidget(self.preview_label)

        # 图片信息
        self.info_label = QLabel("")
        left_layout.addWidget(self.info_label)

        layout.addLayout(left_layout, 1)

        # 右侧：控制面板
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)

        # 文件操作
        file_group = QGroupBox("文件")
        file_layout = QVBoxLayout(file_group)

        open_btn = QPushButton("打开图片")
        open_btn.clicked.connect(self._on_open_image)
        file_layout.addWidget(open_btn)

        self.save_btn = QPushButton("保存裁剪结果")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._on_save)
        file_layout.addWidget(self.save_btn)

        right_layout.addWidget(file_group)

        # 旋转控制
        rotate_group = QGroupBox("旋转")
        rotate_layout = QVBoxLayout(rotate_group)

        rotate_layout.addWidget(QLabel("旋转角度:"))
        self.rotate_combo = QComboBox()
        self.rotate_combo.addItems(["0°", "90°", "180°", "270°"])
        self.rotate_combo.currentIndexChanged.connect(self._on_rotate)
        rotate_layout.addWidget(self.rotate_combo)

        # 快速旋转按钮
        rotate_btn_layout = QHBoxLayout()
        rotate_left_btn = QPushButton("↺ 左转90°")
        rotate_left_btn.clicked.connect(lambda: self._rotate_by(-90))
        rotate_btn_layout.addWidget(rotate_left_btn)

        rotate_right_btn = QPushButton("↻ 右转90°")
        rotate_right_btn.clicked.connect(lambda: self._rotate_by(90))
        rotate_btn_layout.addWidget(rotate_right_btn)
        rotate_layout.addLayout(rotate_btn_layout)

        right_layout.addWidget(rotate_group)

        # 裁剪控制
        crop_group = QGroupBox("裁剪")
        crop_layout = QFormLayout(crop_group)

        self.crop_x = ArrowSpinBox()
        self.crop_x.setRange(0, 9999)
        self.crop_x.valueChanged.connect(self._on_crop_changed)
        crop_layout.addRow("X:", self.crop_x)

        self.crop_y = ArrowSpinBox()
        self.crop_y.setRange(0, 9999)
        self.crop_y.valueChanged.connect(self._on_crop_changed)
        crop_layout.addRow("Y:", self.crop_y)

        self.crop_w = ArrowSpinBox()
        self.crop_w.setRange(1, 9999)
        self.crop_w.valueChanged.connect(self._on_crop_changed)
        crop_layout.addRow("宽度:", self.crop_w)

        self.crop_h = ArrowSpinBox()
        self.crop_h.setRange(1, 9999)
        self.crop_h.valueChanged.connect(self._on_crop_changed)
        crop_layout.addRow("高度:", self.crop_h)

        # 预设比例
        self.ratio_combo = QComboBox()
        self.ratio_combo.addItems(["自由裁剪", "1:1", "4:3", "3:4", "16:9", "9:16"])
        self.ratio_combo.currentTextChanged.connect(self._on_ratio_changed)
        crop_layout.addRow("比例:", self.ratio_combo)

        right_layout.addWidget(crop_group)

        # 操作按钮
        btn_layout = QVBoxLayout()

        reset_btn = QPushButton("重置")
        reset_btn.clicked.connect(self._on_reset)
        btn_layout.addWidget(reset_btn)

        apply_btn = QPushButton("应用裁剪")
        apply_btn.clicked.connect(self._on_apply_crop)
        btn_layout.addWidget(apply_btn)

        right_layout.addLayout(btn_layout)

        right_layout.addStretch()

        # 确定取消
        confirm_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        confirm_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        confirm_layout.addWidget(cancel_btn)
        right_layout.addLayout(confirm_layout)

        layout.addLayout(right_layout)

    def _load_image(self, path: str):
        """加载图片"""
        try:
            self._original_image = Image.open(path)
            self._current_image = self._original_image.copy()
            self._rotation = 0
            self.rotate_combo.setCurrentIndex(0)

            # 更新裁剪范围
            w, h = self._current_image.size
            self.crop_x.setMaximum(w)
            self.crop_y.setMaximum(h)
            self.crop_w.setMaximum(w)
            self.crop_h.setMaximum(h)
            self.crop_w.setValue(w)
            self.crop_h.setValue(h)

            self._update_preview()
            self.save_btn.setEnabled(True)
            self.info_label.setText(f"原图尺寸: {w} x {h}")

        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法加载图片: {e}")

    def _on_open_image(self):
        """打开图片文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "",
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif);;所有文件 (*)"
        )
        if file_path:
            self._image_path = file_path
            self._load_image(file_path)

    def _update_preview(self):
        """更新预览"""
        if self._current_image is None:
            return

        # 获取裁剪区域
        x = self.crop_x.value()
        y = self.crop_y.value()
        w = self.crop_w.value()
        h = self.crop_h.value()

        # 确保裁剪区域有效
        img_w, img_h = self._current_image.size
        x = min(x, img_w - 1)
        y = min(y, img_h - 1)
        w = min(w, img_w - x)
        h = min(h, img_h - y)

        # 创建预览图（带裁剪框）
        preview_img = self._current_image.copy()

        # 缩放到适合预览区域
        max_w, max_h = 480, 380
        scale = min(max_w / preview_img.width, max_h / preview_img.height)
        if scale < 1:
            new_size = (int(preview_img.width * scale), int(preview_img.height * scale))
            preview_img = preview_img.resize(new_size, Image.Resampling.LANCZOS)
            # 调整裁剪框坐标
            x = int(x * scale)
            y = int(y * scale)
            w = int(w * scale)
            h = int(h * scale)

        # 转换为Qt格式并绘制裁剪框
        qimg = self._pil_to_qimage(preview_img)
        pixmap = QPixmap.fromImage(qimg)

        # 绘制裁剪框
        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor(255, 0, 0), 2, Qt.DashLine))
        painter.drawRect(x, y, w, h)

        # 绘制半透明遮罩
        painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
        painter.setPen(Qt.NoPen)
        # 上
        painter.drawRect(0, 0, pixmap.width(), y)
        # 下
        painter.drawRect(0, y + h, pixmap.width(), pixmap.height() - y - h)
        # 左
        painter.drawRect(0, y, x, h)
        # 右
        painter.drawRect(x + w, y, pixmap.width() - x - w, h)

        painter.end()

        self.preview_label.setPixmap(pixmap)

    def _pil_to_qimage(self, pil_image: Image.Image) -> QImage:
        """PIL图片转QImage"""
        if pil_image.mode == 'RGB':
            data = pil_image.tobytes('raw', 'RGB')
            qimg = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGB888)
        elif pil_image.mode == 'RGBA':
            data = pil_image.tobytes('raw', 'RGBA')
            qimg = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGBA8888)
        else:
            pil_image = pil_image.convert('RGB')
            data = pil_image.tobytes('raw', 'RGB')
            qimg = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGB888)
        return qimg

    def _on_rotate(self, index):
        """旋转角度改变"""
        if self._original_image is None:
            return

        angles = [0, 90, 180, 270]
        self._rotation = angles[index]

        self._current_image = self._original_image.copy()
        if self._rotation != 0:
            self._current_image = self._current_image.rotate(-self._rotation, expand=True)

        # 更新裁剪范围
        w, h = self._current_image.size
        self.crop_x.setMaximum(w)
        self.crop_y.setMaximum(h)
        self.crop_w.setMaximum(w)
        self.crop_h.setMaximum(h)
        self.crop_x.setValue(0)
        self.crop_y.setValue(0)
        self.crop_w.setValue(w)
        self.crop_h.setValue(h)

        self._update_preview()

    def _rotate_by(self, angle: int):
        """按指定角度旋转"""
        current_index = self.rotate_combo.currentIndex()
        angles = [0, 90, 180, 270]
        current_angle = angles[current_index]
        new_angle = (current_angle + angle) % 360
        new_index = angles.index(new_angle)
        self.rotate_combo.setCurrentIndex(new_index)

    def _on_crop_changed(self):
        """裁剪参数改变"""
        self._update_preview()

    def _on_ratio_changed(self, ratio_text: str):
        """裁剪比例改变"""
        if ratio_text == "自由裁剪" or self._current_image is None:
            return

        ratios = {
            "1:1": (1, 1),
            "4:3": (4, 3),
            "3:4": (3, 4),
            "16:9": (16, 9),
            "9:16": (9, 16),
        }

        if ratio_text in ratios:
            rw, rh = ratios[ratio_text]
            img_w, img_h = self._current_image.size

            # 计算最大裁剪区域
            if img_w / img_h > rw / rh:
                # 图片更宽，以高度为准
                h = img_h
                w = int(h * rw / rh)
            else:
                # 图片更高，以宽度为准
                w = img_w
                h = int(w * rh / rw)

            self.crop_w.setValue(w)
            self.crop_h.setValue(h)
            self.crop_x.setValue((img_w - w) // 2)
            self.crop_y.setValue((img_h - h) // 2)

            self._update_preview()

    def _on_apply_crop(self):
        """应用裁剪"""
        if self._current_image is None:
            return

        x = self.crop_x.value()
        y = self.crop_y.value()
        w = self.crop_w.value()
        h = self.crop_h.value()

        try:
            self._current_image = self._current_image.crop((x, y, x + w, y + h))

            # 更新范围
            new_w, new_h = self._current_image.size
            self.crop_x.setMaximum(new_w)
            self.crop_y.setMaximum(new_h)
            self.crop_w.setMaximum(new_w)
            self.crop_h.setMaximum(new_h)
            self.crop_x.setValue(0)
            self.crop_y.setValue(0)
            self.crop_w.setValue(new_w)
            self.crop_h.setValue(new_h)

            self._update_preview()
            self.info_label.setText(f"裁剪后尺寸: {new_w} x {new_h}")

        except Exception as e:
            QMessageBox.warning(self, "错误", f"裁剪失败: {e}")

    def _on_reset(self):
        """重置"""
        if self._original_image is None:
            return

        self._current_image = self._original_image.copy()
        self._rotation = 0
        self.rotate_combo.setCurrentIndex(0)

        w, h = self._current_image.size
        self.crop_x.setValue(0)
        self.crop_y.setValue(0)
        self.crop_w.setValue(w)
        self.crop_h.setValue(h)
        self.ratio_combo.setCurrentIndex(0)

        self._update_preview()
        self.info_label.setText(f"原图尺寸: {w} x {h}")

    def _on_save(self):
        """保存裁剪结果"""
        if self._current_image is None:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存图片",
            Path(self._image_path).stem + "_cropped.png",
            "PNG图片 (*.png);;JPEG图片 (*.jpg);;所有文件 (*)"
        )

        if file_path:
            try:
                self._current_image.save(file_path)
                QMessageBox.information(self, "成功", f"图片已保存到:\n{file_path}")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"保存失败: {e}")

    def get_cropped_image(self) -> Optional[Image.Image]:
        """获取裁剪后的图片"""
        return self._current_image

    def get_cropped_path(self) -> Optional[str]:
        """获取裁剪后图片的保存路径"""
        return self._image_path
