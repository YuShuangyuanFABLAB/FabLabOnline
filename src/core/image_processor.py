# -*- coding: utf-8 -*-
"""
图片处理器
负责图片的加载、裁剪、缩放等处理
"""

from pathlib import Path
from typing import Optional, Tuple, List
import io

from PIL import Image


class ImageProcessor:
    """图片处理器类"""

    # 默认目标尺寸（英寸）
    DEFAULT_WIDTH = 6.55
    DEFAULT_HEIGHT = 8.07

    # DPI（每英寸点数）
    DPI = 96

    # 支持的图片格式
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}

    def __init__(self):
        """初始化图片处理器"""
        pass

    def is_supported_format(self, file_path: str) -> bool:
        """
        检查文件格式是否支持

        Args:
            file_path: 文件路径

        Returns:
            是否支持
        """
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_FORMATS

    def load_image(self, image_path: str) -> Optional[Image.Image]:
        """
        加载图片

        Args:
            image_path: 图片路径

        Returns:
            PIL Image对象，失败返回None
        """
        try:
            path = Path(image_path)
            if not path.exists():
                print(f"图片文件不存在: {image_path}")
                return None

            if not self.is_supported_format(image_path):
                print(f"不支持的图片格式: {path.suffix}")
                return None

            img = Image.open(path)

            # 转换为RGB模式（处理RGBA等）
            if img.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if img.mode in ('RGBA', 'LA'):
                    background.paste(img, mask=img.split()[-1])
                    img = background
                else:
                    img = img.convert('RGB')

            return img
        except Exception as e:
            print(f"加载图片失败: {e}")
            return None

    def load_image_from_bytes(self, image_bytes: bytes) -> Optional[Image.Image]:
        """
        从字节数据加载图片

        Args:
            image_bytes: 图片字节数据

        Returns:
            PIL Image对象，失败返回None
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))
            return img
        except Exception as e:
            print(f"从字节加载图片失败: {e}")
            return None

    def get_image_info(self, image_path: str) -> Optional[dict]:
        """
        获取图片信息

        Args:
            image_path: 图片路径

        Returns:
            图片信息字典
        """
        img = self.load_image(image_path)
        if img is None:
            return None

        return {
            "width": img.width,
            "height": img.height,
            "mode": img.mode,
            "format": img.format,
            "size_bytes": Path(image_path).stat().st_size if Path(image_path).exists() else 0
        }

    def inches_to_pixels(self, inches: float) -> int:
        """
        英寸转换为像素

        Args:
            inches: 英寸值

        Returns:
            像素值
        """
        return int(inches * self.DPI)

    def pixels_to_inches(self, pixels: int) -> float:
        """
        像素转换为英寸

        Args:
            pixels: 像素值

        Returns:
            英寸值
        """
        return pixels / self.DPI

    def resize_to_fit(
        self,
        img: Image.Image,
        target_width: float,
        target_height: float
    ) -> Image.Image:
        """
        调整图片大小以适配目标区域（保持宽高比，覆盖整个区域）

        Args:
            img: PIL Image对象
            target_width: 目标宽度（英寸）
            target_height: 目标高度（英寸）

        Returns:
            调整后的Image对象
        """
        # 转换为像素
        target_w_px = self.inches_to_pixels(target_width)
        target_h_px = self.inches_to_pixels(target_height)

        # 计算缩放比例（选择较大的比例以覆盖整个区域）
        width_ratio = target_w_px / img.width
        height_ratio = target_h_px / img.height
        scale = max(width_ratio, height_ratio)

        # 计算新尺寸
        new_width = int(img.width * scale)
        new_height = int(img.height * scale)

        # 缩放图片
        resized = img.resize((new_width, new_height), Image.LANCZOS)
        return resized

    def resize_to_contain(
        self,
        img: Image.Image,
        target_width: float,
        target_height: float
    ) -> Image.Image:
        """
        调整图片大小以完全包含在目标区域内（保持宽高比）

        Args:
            img: PIL Image对象
            target_width: 目标宽度（英寸）
            target_height: 目标高度（英寸）

        Returns:
            调整后的Image对象
        """
        target_w_px = self.inches_to_pixels(target_width)
        target_h_px = self.inches_to_pixels(target_height)

        # 选择较小的比例以完全包含
        width_ratio = target_w_px / img.width
        height_ratio = target_h_px / img.height
        scale = min(width_ratio, height_ratio)

        new_width = int(img.width * scale)
        new_height = int(img.height * scale)

        resized = img.resize((new_width, new_height), Image.LANCZOS)
        return resized

    def center_crop(
        self,
        img: Image.Image,
        target_width: float,
        target_height: float
    ) -> Image.Image:
        """
        居中裁剪图片

        Args:
            img: PIL Image对象
            target_width: 目标宽度（英寸）
            target_height: 目标高度（英寸）

        Returns:
            裁剪后的Image对象
        """
        target_w_px = self.inches_to_pixels(target_width)
        target_h_px = self.inches_to_pixels(target_height)

        # 确保图片足够大
        if img.width < target_w_px or img.height < target_h_px:
            # 如果图片太小，先放大
            img = self.resize_to_fit(img, target_width, target_height)

        # 计算裁剪位置
        left = (img.width - target_w_px) // 2
        top = (img.height - target_h_px) // 2
        right = left + target_w_px
        bottom = top + target_h_px

        # 裁剪
        cropped = img.crop((left, top, right, bottom))
        return cropped

    def custom_crop(
        self,
        img: Image.Image,
        crop_x: float,
        crop_y: float,
        crop_width: float,
        crop_height: float,
        target_width: float,
        target_height: float
    ) -> Image.Image:
        """
        自定义裁剪

        Args:
            img: PIL Image对象
            crop_x: 裁剪起始X（比例，0-1）
            crop_y: 裁剪起始Y（比例，0-1）
            crop_width: 裁剪宽度（比例，0-1）
            crop_height: 裁剪高度（比例，0-1）
            target_width: 目标宽度（英寸）
            target_height: 目标高度（英寸）

        Returns:
            裁剪后的Image对象
        """
        # 计算像素坐标
        left = int(img.width * crop_x)
        top = int(img.height * crop_y)
        right = int(img.width * (crop_x + crop_width))
        bottom = int(img.height * (crop_y + crop_height))

        # 裁剪
        cropped = img.crop((left, top, right, bottom))

        # 调整到目标尺寸
        target_w_px = self.inches_to_pixels(target_width)
        target_h_px = self.inches_to_pixels(target_height)
        resized = cropped.resize((target_w_px, target_h_px), Image.LANCZOS)

        return resized

    def process_image(
        self,
        image_path: str,
        target_width: float = DEFAULT_WIDTH,
        target_height: float = DEFAULT_HEIGHT,
        mode: str = "center"
    ) -> Optional[Image.Image]:
        """
        完整的图片处理流程

        Args:
            image_path: 图片路径
            target_width: 目标宽度（英寸）
            target_height: 目标高度（英寸）
            mode: 裁剪模式（center/manual）

        Returns:
            处理后的Image对象
        """
        img = self.load_image(image_path)
        if img is None:
            return None

        # 调整大小
        resized = self.resize_to_fit(img, target_width, target_height)

        # 居中裁剪
        if mode == "center":
            result = self.center_crop(resized, target_width, target_height)
        else:
            result = resized

        return result

    def process_image_for_ppt(
        self,
        image_path: str,
        layout_type: str = "model"
    ) -> Optional[Image.Image]:
        """
        为PPT处理图片（根据布局类型选择尺寸）

        Args:
            image_path: 图片路径
            layout_type: 布局类型（model, work, double_image等）

        Returns:
            处理后的Image对象
        """
        # 不同布局的目标尺寸（英寸）
        layout_sizes = {
            "model": (6.55, 8.07),
            "work": (6.55, 8.07),
            "double_image": (3.2, 4.0),  # 双图布局，每张图较小
            "program": (6.55, 8.07),
            "vehicle": (6.55, 8.07),
        }

        target_width, target_height = layout_sizes.get(layout_type, (self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT))

        return self.process_image(image_path, target_width, target_height)

    def rotate(self, img: Image.Image, degrees: int = 90) -> Image.Image:
        """
        旋转图片

        Args:
            img: PIL Image对象
            degrees: 旋转角度（90的倍数）

        Returns:
            旋转后的Image对象
        """
        return img.rotate(-degrees, expand=True)

    def flip_horizontal(self, img: Image.Image) -> Image.Image:
        """
        水平翻转图片

        Args:
            img: PIL Image对象

        Returns:
            翻转后的Image对象
        """
        return img.transpose(Image.FLIP_LEFT_RIGHT)

    def flip_vertical(self, img: Image.Image) -> Image.Image:
        """
        垂直翻转图片

        Args:
            img: PIL Image对象

        Returns:
            翻转后的Image对象
        """
        return img.transpose(Image.FLIP_TOP_BOTTOM)

    def save_image(
        self,
        img: Image.Image,
        output_path: str,
        format: str = "PNG",
        quality: int = 95
    ) -> bool:
        """
        保存图片

        Args:
            img: PIL Image对象
            output_path: 输出路径
            format: 图片格式
            quality: 质量（1-100，仅对JPEG有效）

        Returns:
            是否成功
        """
        try:
            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            if format.upper() == "JPEG":
                img.save(output_path, format="JPEG", quality=quality)
            else:
                img.save(output_path, format=format)

            return True
        except Exception as e:
            print(f"保存图片失败: {e}")
            return False

    def image_to_bytes(self, img: Image.Image, format: str = "PNG") -> Optional[bytes]:
        """
        将图片转换为字节数据

        Args:
            img: PIL Image对象
            format: 图片格式

        Returns:
            字节数据
        """
        try:
            buffer = io.BytesIO()
            if format.upper() == "JPEG":
                img.save(buffer, format="JPEG", quality=95)
            else:
                img.save(buffer, format=format)
            return buffer.getvalue()
        except Exception as e:
            print(f"转换图片为字节失败: {e}")
            return None

    def create_thumbnail(
        self,
        image_path: str,
        max_size: Tuple[int, int] = (200, 200)
    ) -> Optional[Image.Image]:
        """
        创建缩略图

        Args:
            image_path: 图片路径
            max_size: 最大尺寸

        Returns:
            缩略图Image对象
        """
        img = self.load_image(image_path)
        if img is None:
            return None

        img.thumbnail(max_size, Image.LANCZOS)
        return img

    def batch_process(
        self,
        image_paths: List[str],
        target_width: float = DEFAULT_WIDTH,
        target_height: float = DEFAULT_HEIGHT,
        mode: str = "center"
    ) -> List[Optional[Image.Image]]:
        """
        批量处理图片

        Args:
            image_paths: 图片路径列表
            target_width: 目标宽度（英寸）
            target_height: 目标高度（英寸）
            mode: 裁剪模式

        Returns:
            处理后的Image对象列表
        """
        results = []
        for path in image_paths:
            result = self.process_image(path, target_width, target_height, mode)
            results.append(result)
        return results
