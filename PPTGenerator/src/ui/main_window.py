# -*- coding: utf-8 -*-
"""
主窗口模块
法贝实验室课程反馈助手的主界面
"""

import sys
import os
import shutil
import re
from pathlib import Path
from typing import Optional, List, Dict

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QAction, QStatusBar, QToolBar, QSplitter,
    QMessageBox, QFileDialog, QLabel, QTabWidget,
    QPushButton, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeySequence, QFont

# 路径适配 - 兼容开发和打包环境
def get_base_path() -> Path:
    """获取应用程序基础路径"""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent.parent

def get_app_dir() -> Path:
    """获取应用程序所在目录"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent.parent

# 添加项目根目录到路径
sys.path.insert(0, str(get_base_path()))

from src.core.config_manager import ConfigManager
from src.core.models import CourseUnitData, LayoutConfig
from src.core.ppt_generator import PPTGenerator

from src.ui.widgets.layout_selector import LayoutSelectorWidget
from src.ui.widgets.course_info import CourseInfoWidget
from src.ui.widgets.evaluation import EvaluationWidget
from src.ui.widgets.image_upload import ImageUploadWidget
from src.ui.widgets.rich_text_editor import RichTextEditor
from src.ui.widgets.series_selector import SeriesSelectorWidget
from src.ui.widgets.class_selector import ClassSelectorWidget
from src.ui.widgets.student_manager import StudentManagerWidget
from src.ui.widgets.student_tab_bar import StudentTabBar
from src.ui.dialogs.batch_progress_dialog import BatchProgressDialog
from src.ui.dialogs.config_transfer_dialog import ConfigTransferDialog
from src.ui.theme import ThemeManager


# ==================== 字体检测和安装功能 ====================

def check_system_font(font_name: str) -> bool:
    """
    检查系统是否安装了指定字体

    Args:
        font_name: 字体名称（如 "华文琥珀"）

    Returns:
        bool: 是否已安装
    """
    # Windows 字体目录
    fonts_dir = Path(os.environ.get('SystemRoot', 'C:\\Windows')) / 'Fonts'

    # 检查常见字体文件名
    font_mappings = {
        '华文琥珀': ['STHUPO.TTF', 'stliti.ttf'],
        '等线': ['DENGXIAN.TTF', 'Dengxian.ttf'],
    }

    if font_name in font_mappings:
        for font_file in font_mappings[font_name]:
            if (fonts_dir / font_file).exists():
                return True

    # 尝试通过 QFont 检测
    font = QFont(font_name)
    return font.exactMatch()


def get_missing_fonts() -> List[str]:
    """
    获取缺失的字体列表

    Returns:
        List[str]: 缺失的字体名称列表
    """
    required_fonts = ['华文琥珀']  # 等线在 Windows 10+ 自带
    missing = []
    for font in required_fonts:
        if not check_system_font(font):
            missing.append(font)
    return missing


def install_font(font_path: Path) -> bool:
    """
    安装字体到用户字体目录（不需要管理员权限）

    Args:
        font_path: 字体文件路径

    Returns:
        bool: 是否安装成功
    """
    try:
        # 用户字体目录
        user_fonts_dir = Path.home() / 'AppData' / 'Local' / 'Microsoft' / 'Windows' / 'Fonts'
        user_fonts_dir.mkdir(parents=True, exist_ok=True)

        # 复制字体文件
        dest_path = user_fonts_dir / font_path.name
        shutil.copy2(font_path, dest_path)

        # 注册字体（用户级别）
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts',
            0, winreg.KEY_SET_VALUE
        )
        font_name = font_path.stem
        winreg.SetValueEx(key, f'{font_name} (TrueType)', 0, winreg.REG_SZ, str(dest_path))
        winreg.CloseKey(key)

        return True
    except Exception as e:
        print(f"安装字体失败: {e}")
        return False


class FontMissingDialog(QDialog):
    """字体缺失提示对话框"""

    def __init__(self, missing_fonts: List[str], fonts_dir: Path, parent=None):
        super().__init__(parent)
        self.fonts_dir = fonts_dir
        self.missing_fonts = missing_fonts
        self.install_success = False

        self.setWindowTitle("字体检测")
        self.setMinimumWidth(400)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # 提示信息
        font_list = "、".join(missing_fonts)
        info_label = QLabel(
            f"检测到系统缺少以下字体：\n\n{font_list}\n\n"
            "缺少字体会导致PPT显示异常。\n\n"
            "是否立即安装字体？"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # 按钮
        btn_layout = QHBoxLayout()

        install_btn = QPushButton("安装字体")
        install_btn.clicked.connect(self._install_fonts)
        btn_layout.addWidget(install_btn)

        skip_btn = QPushButton("暂不安装")
        skip_btn.clicked.connect(self.reject)
        btn_layout.addWidget(skip_btn)

        layout.addLayout(btn_layout)

    def _install_fonts(self):
        """安装字体"""
        success_count = 0

        # 字体文件映射
        font_files = {
            '华文琥珀': 'STHUPO.TTF',
        }

        for font_name in self.missing_fonts:
            if font_name in font_files:
                font_path = self.fonts_dir / font_files[font_name]
                if font_path.exists():
                    if install_font(font_path):
                        success_count += 1

        if success_count == len(self.missing_fonts):
            self.install_success = True
            QMessageBox.information(
                self, "安装成功",
                "字体安装成功！\n\n请注意：部分应用可能需要重启才能识别新字体。\n"
                "建议重启本程序以确保字体生效。"
            )
            self.accept()
        else:
            QMessageBox.warning(
                self, "安装失败",
                "部分字体安装失败。\n\n您可以手动双击字体文件进行安装。"
            )
            self.reject()


class MainWindow(QMainWindow):
    """主窗口类"""

    # 信号
    data_changed = pyqtSignal()

    # 共享字段名称（班级内所有学员同步）
    _SHARED_FIELDS = [
        'knowledge_content', 'knowledge_html',
        'highlights', 'difficulties',
        'homework', 'other_notes',
        # 图片字段的同步由 _image_sync_states 动态控制
        'course_content',    # 课程内容在班级内同步
        'teacher_name',      # 授课教师在班级内同步
        # 注意：student_name 不应共享，因为每个学生不同
        # 注意：work_images 始终独立，每个学员有自己的精彩瞬间
    ]

    def __init__(self):
        super().__init__()

        # 检测字体（打包环境）
        if getattr(sys, 'frozen', False):
            missing_fonts = get_missing_fonts()
            if missing_fonts:
                fonts_dir = get_base_path() / 'fonts'
                if fonts_dir.exists():
                    dialog = FontMissingDialog(missing_fonts, fonts_dir, self)
                    dialog.exec_()

        # 初始化配置管理器
        self.config_manager = ConfigManager()

        # PPT生成器
        self.ppt_generator: Optional[PPTGenerator] = None

        # 当前数据
        self.current_data = CourseUnitData()
        self.current_layout_config = LayoutConfig()

        # 学员数据缓存：{学员姓名: CourseUnitData}
        self._student_data_cache: dict = {}
        # 当前学员姓名
        self._current_student_name: str = ""
        # 当前班级ID（用于在切换班级时保存课时编号）
        self._current_class_id: str = ""
        # 是否正在加载学员数据（阻止 data_changed 信号）
        self._loading_student_data: bool = False
        # 班级共享数据（同一班级内所有学员同步）
        self._class_shared_data: Optional[CourseUnitData] = None
        # 是否正在同步共享数据（防止循环触发）
        self._syncing_shared_data: bool = False

        # 补充说明同步状态
        self._comments_sync_source: str = ""           # 首位填写补充说明的学员姓名
        self._comments_sync_locked: bool = False       # 是否锁定（有其他人修改过）
        self._comments_sync_content: str = ""          # 同步的原始内容（用于检测变化）
        self._synced_comments_cache: set = set()       # 同步补充说明的缓存标记（学员名集合）

        # 本次会话已生成过PPT的学员集合（用于关闭时决定是否+1）
        self._session_generated_students: set = set()

        # 会话中每个学员首次加载时的补充说明（用于检查是否修改）
        self._session_initial_comments: dict = {}  # {学员名: 初始补充说明}

        # 图片同步状态（可独立控制每类图片的同步）
        self._image_sync_states: Dict[str, bool] = {
            'model_images': True,
            'program_images': True,
            'vehicle_images': True,
        }

        # 初始化UI
        self._init_ui()
        self._init_menu()
        self._init_toolbar()
        self._init_statusbar()
        self._restore_window_state()
        self._init_ppt_generator()
        self._init_default_values()

        # 设置窗口属性
        self.setWindowTitle("法贝实验室课程反馈助手")
        self.setMinimumSize(1200, 800)

    def _init_ppt_generator(self):
        """初始化PPT生成器"""
        try:
            template_path = self.config_manager.get_template_path()
            # 将相对路径转换为绝对路径（兼容打包环境）
            if not Path(template_path).is_absolute():
                template_path = str(get_base_path() / template_path)
            self.ppt_generator = PPTGenerator(template_path)
            self.update_status("模板加载成功")
        except Exception as e:
            self.update_status(f"模板加载失败: {e}")

    def _init_default_values(self):
        """初始化默认值"""
        # 加载默认班级的学员和老师
        current_class_id = self.class_selector.get_current_class_id()
        # 初始化当前班级ID
        self._current_class_id = current_class_id or ""

        if current_class_id:
            # 恢复班级关联的系列
            series_index = self.config_manager.get_class_series_index(current_class_id)
            self.series_selector.set_series_silently(series_index)

            # 设置课程内容为"系列名(x阶)"格式
            series_name, series_level = self.series_selector.get_current_series()
            if series_name and series_level:
                course_content = f"{series_name}（{series_level}阶）"
            else:
                course_content = series_name
            self.course_info_widget.course_content.setText(course_content)

            # 课时编号改为学员独立，在学员标签切换时加载
            self.student_manager.load_students(current_class_id)
            # 初始化标签栏
            students = self.config_manager.get_students_by_class(current_class_id)
            self.student_tab_bar.load_students(students)
            current_class = self.config_manager.get_current_class()
            teacher = current_class.get("teacher", "")
            if teacher:
                self.course_info_widget.teacher_name.setText(teacher)
            # 自动填充上课时间
            class_name = current_class.get("name", "")
            time_info = ClassSelectorWidget.parse_class_name(class_name)
            if time_info:
                self.course_info_widget.set_class_time(
                    time_info["weekday"],
                    time_info["hour"],
                    time_info["minute"]
                )

            # 加载班级的母版配置
            layout_config = self.config_manager.get_class_layout_config(current_class_id)
            if layout_config:
                self.layout_selector.set_config(layout_config)
                self._update_image_widget_visibility(layout_config)
        else:
            # 没有选中班级时，使用默认系列
            series_name, series_level = self.series_selector.get_current_series()
            if series_name and series_level:
                course_content = f"{series_name}（{series_level}阶）"
            else:
                course_content = series_name
            self.course_info_widget.course_content.setText(course_content)

    def _init_ui(self):
        """初始化UI布局"""
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)

        # ==================== 左侧面板 - 输入区域 ====================
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 创建标签页
        tab_widget = QTabWidget()

        # 标签0: 系列选择（放在最前面）
        series_tab = QWidget()
        series_layout = QVBoxLayout(series_tab)
        series_layout.setContentsMargins(0, 0, 0, 0)

        self.series_selector = SeriesSelectorWidget(self.config_manager)
        self.series_selector.series_changed.connect(self._on_series_changed)
        series_layout.addWidget(self.series_selector)

        # 班级选择器
        self.class_selector = ClassSelectorWidget(self.config_manager)
        self.class_selector.class_changed.connect(self._on_class_changed)
        self.class_selector.teacher_changed.connect(self._on_teacher_changed)
        self.class_selector.class_series_changed.connect(self._on_class_series_changed)
        series_layout.addWidget(self.class_selector)

        # 学员管理器
        self.student_manager = StudentManagerWidget(self.config_manager)
        self.student_manager.student_selected.connect(self._on_student_selected)
        self.student_manager.students_changed.connect(self._on_students_changed)
        series_layout.addWidget(self.student_manager)

        series_layout.addStretch()

        tab_widget.addTab(series_tab, "系列选择")

        # 标签1: 基本信息
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)

        # 课程信息组件
        self.course_info_widget = CourseInfoWidget(
            recent_students=self.config_manager.get_recent_students(),
            recent_teachers=self.config_manager.get_recent_teachers()
        )
        self.course_info_widget.data_changed.connect(self._on_data_changed)
        basic_layout.addWidget(self.course_info_widget)

        # 母版选择组件
        self.layout_selector = LayoutSelectorWidget()
        self.layout_selector.set_config(self.config_manager.get_layout_config())
        self.layout_selector.config_changed.connect(self._on_layout_changed)
        basic_layout.addWidget(self.layout_selector)

        basic_layout.addStretch()
        tab_widget.addTab(basic_tab, "基本信息")

        # 标签2: 课堂知识
        knowledge_tab = QWidget()
        knowledge_layout = QVBoxLayout(knowledge_tab)
        knowledge_layout.setContentsMargins(5, 5, 5, 5)

        # 知识内容富文本编辑器
        knowledge_label = QLabel("课堂知识内容")
        knowledge_label.setStyleSheet("font-weight: bold;")
        knowledge_layout.addWidget(knowledge_label)

        hint_label = QLabel("提示：选中文字后点击\"重点\"标记为蓝色，点击\"难点\"标记为橙色")
        hint_label.setStyleSheet("color: #666; font-size: 11px;")
        knowledge_layout.addWidget(hint_label)

        self.knowledge_editor = RichTextEditor(placeholder="请输入课堂知识内容...")
        self.knowledge_editor.text_changed.connect(self._on_data_changed)
        knowledge_layout.addWidget(self.knowledge_editor)

        tab_widget.addTab(knowledge_tab, "课堂知识")

        # 标签3: 评价
        eval_tab = QWidget()
        eval_layout = QVBoxLayout(eval_tab)
        eval_layout.setContentsMargins(0, 0, 0, 0)

        self.evaluation_widget = EvaluationWidget()
        self.evaluation_widget.data_changed.connect(self._on_data_changed)
        self.evaluation_widget.sync_comments_requested.connect(self._force_sync_comments)
        eval_layout.addWidget(self.evaluation_widget)

        tab_widget.addTab(eval_tab, "课堂评价")

        # 标签4: 图片
        image_tab = QWidget()
        image_layout = QVBoxLayout(image_tab)
        image_layout.setContentsMargins(5, 5, 5, 5)

        # 模型展示图片（带同步按钮）
        self.model_image_widget = ImageUploadWidget("模型展示图片", max_images=9, show_sync_button=True)
        self.model_image_widget.images_changed.connect(self._on_images_changed)
        self.model_image_widget.sync_toggled.connect(self._on_model_image_sync_toggled)
        image_layout.addWidget(self.model_image_widget)

        # 程序展示图片（带同步按钮）
        self.program_image_widget = ImageUploadWidget("程序展示图片", max_images=9, show_sync_button=True)
        self.program_image_widget.images_changed.connect(self._on_images_changed)
        self.program_image_widget.sync_toggled.connect(self._on_program_image_sync_toggled)
        image_layout.addWidget(self.program_image_widget)

        # 车辆展示图片（带同步按钮）
        self.vehicle_image_widget = ImageUploadWidget("车辆展示图片", max_images=9, show_sync_button=True)
        self.vehicle_image_widget.images_changed.connect(self._on_images_changed)
        self.vehicle_image_widget.sync_toggled.connect(self._on_vehicle_image_sync_toggled)
        image_layout.addWidget(self.vehicle_image_widget)

        # 精彩瞬间图片（不显示同步按钮，始终独立）
        self.work_image_widget = ImageUploadWidget("精彩瞬间图片", max_images=9)
        self.work_image_widget.images_changed.connect(self._on_images_changed)
        image_layout.addWidget(self.work_image_widget)

        image_layout.addStretch()
        tab_widget.addTab(image_tab, "图片上传")

        left_layout.addWidget(tab_widget)

        # 学员选择标签栏
        self.student_tab_bar = StudentTabBar()
        self.student_tab_bar.student_tab_changed.connect(self._on_student_tab_changed)
        left_layout.addWidget(self.student_tab_bar)

        # 添加到分割器（只保留左侧面板）
        splitter.addWidget(left_panel)

        main_layout.addWidget(splitter)

        # 保存分割器引用
        self.splitter = splitter

        # 设置初始可见性（根据默认布局配置）
        self._update_image_widget_visibility(self.config_manager.get_layout_config())

    def _init_menu(self):
        """初始化菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        new_action = QAction("新建(&N)", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.setStatusTip("创建新的课程反馈")
        new_action.triggered.connect(self._on_new)
        file_menu.addAction(new_action)

        open_action = QAction("打开(&O)", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.setStatusTip("打开已保存的课程数据")
        open_action.triggered.connect(self._on_open)
        file_menu.addAction(open_action)

        save_action = QAction("保存(&S)", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.setStatusTip("保存当前课程数据")
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        import_excel_action = QAction("导入Excel(&I)", self)
        import_excel_action.setShortcut(QKeySequence("Ctrl+I"))
        import_excel_action.setStatusTip("从Excel文件导入课程数据")
        import_excel_action.triggered.connect(self._on_import_excel)
        file_menu.addAction(import_excel_action)

        file_menu.addSeparator()

        export_config_action = QAction("导出配置(&E)", self)
        export_config_action.setStatusTip("导出所有配置到文件，方便迁移到其他电脑")
        export_config_action.triggered.connect(self._on_export_config)
        file_menu.addAction(export_config_action)

        import_config_action = QAction("导入配置(&M)", self)
        import_config_action.setStatusTip("从文件导入配置（班级、学员、评价等）")
        import_config_action.triggered.connect(self._on_import_config)
        file_menu.addAction(import_config_action)

        file_menu.addSeparator()

        generate_action = QAction("生成PPT(&G)", self)
        generate_action.setShortcut(QKeySequence("Ctrl+G"))
        generate_action.setStatusTip("根据当前数据生成PPT文件")
        generate_action.triggered.connect(self._on_generate_ppt)
        file_menu.addAction(generate_action)

        batch_generate_action = QAction("批量生成PPT(&B)", self)
        batch_generate_action.setShortcut(QKeySequence("Ctrl+Shift+B"))
        batch_generate_action.setStatusTip("为选中的学员批量生成PPT文件")
        batch_generate_action.triggered.connect(self._on_batch_generate_ppt)
        file_menu.addAction(batch_generate_action)

        file_menu.addSeparator()

        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip("退出程序")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")

        clear_action = QAction("清空表单(&C)", self)
        clear_action.setStatusTip("清空所有输入内容")
        clear_action.triggered.connect(self._on_clear_form)
        edit_menu.addAction(clear_action)

        reset_action = QAction("重置为默认(&R)", self)
        reset_action.setStatusTip("重置所有设置为默认值")
        reset_action.triggered.connect(self._on_reset_defaults)
        edit_menu.addAction(reset_action)

        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")

        self.toolbar_action = QAction("显示工具栏(&T)", self)
        self.toolbar_action.setCheckable(True)
        self.toolbar_action.setChecked(True)
        self.toolbar_action.triggered.connect(self._on_toggle_toolbar)
        view_menu.addAction(self.toolbar_action)

        self.statusbar_action = QAction("显示状态栏(&S)", self)
        self.statusbar_action.setCheckable(True)
        self.statusbar_action.setChecked(True)
        self.statusbar_action.triggered.connect(self._on_toggle_statusbar)
        view_menu.addAction(self.statusbar_action)

        view_menu.addSeparator()

        # 主题切换
        self.theme_action = QAction("夜间模式(&N)", self)
        self.theme_action.setCheckable(True)
        self.theme_action.setShortcut(QKeySequence("Ctrl+T"))
        self.theme_action.setStatusTip("切换日间/夜间模式")
        self.theme_action.triggered.connect(self._on_toggle_theme)
        view_menu.addAction(self.theme_action)

        # 初始化主题状态
        ThemeManager.instance().theme_changed.connect(self._on_theme_changed)
        saved_theme = self.config_manager.get_theme()
        self.theme_action.setChecked(saved_theme == "dark")
        ThemeManager.instance().set_theme(saved_theme)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        about_action = QAction("关于(&A)", self)
        about_action.setStatusTip("关于本程序")
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _init_toolbar(self):
        """初始化工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setObjectName("mainToolBar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        new_btn = QAction("新建", self)
        new_btn.setStatusTip("新建课程反馈")
        new_btn.triggered.connect(self._on_new)
        toolbar.addAction(new_btn)

        open_btn = QAction("打开", self)
        open_btn.setStatusTip("打开文件")
        open_btn.triggered.connect(self._on_open)
        toolbar.addAction(open_btn)

        save_btn = QAction("保存", self)
        save_btn.setStatusTip("保存文件")
        save_btn.triggered.connect(self._on_save)
        toolbar.addAction(save_btn)

        toolbar.addSeparator()

        generate_btn = QAction("生成PPT", self)
        generate_btn.setStatusTip("生成PPT文件")
        generate_btn.triggered.connect(self._on_generate_ppt)
        toolbar.addAction(generate_btn)

        batch_generate_btn = QAction("批量生成", self)
        batch_generate_btn.setStatusTip("为选中学员批量生成PPT")
        batch_generate_btn.triggered.connect(self._on_batch_generate_ppt)
        toolbar.addAction(batch_generate_btn)

        self.toolbar = toolbar

    def _init_statusbar(self):
        """初始化状态栏"""
        statusbar = QStatusBar()
        self.setStatusBar(statusbar)

        self.status_label = QLabel("就绪")
        statusbar.addWidget(self.status_label, 1)

        self.info_label = QLabel("")
        statusbar.addPermanentWidget(self.info_label)

    def _restore_window_state(self):
        """恢复窗口状态"""
        settings = self.config_manager.settings

        geometry = settings.get("window_geometry")
        if geometry:
            self.restoreGeometry(bytes.fromhex(geometry))

        state = settings.get("window_state")
        if state:
            self.restoreState(bytes.fromhex(state))

        splitter_state = settings.get("splitter_state")
        if splitter_state:
            self.splitter.restoreState(bytes.fromhex(splitter_state))

    def _save_window_state(self):
        """保存窗口状态"""
        settings = self.config_manager.settings

        settings["window_geometry"] = bytes(self.saveGeometry()).hex()
        settings["window_state"] = bytes(self.saveState()).hex()
        settings["splitter_state"] = bytes(self.splitter.saveState()).hex()

        self.config_manager.save_settings()

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 保存当前学员数据（确保评价不丢失）
        self._save_current_student_data()

        # 重置补充说明同步状态
        self._comments_sync_source = ""
        self._comments_sync_locked = False
        self._comments_sync_content = ""

        # 保存所有本次会话生成过PPT的学员的课时编号（+1）
        current_class_id = self.class_selector.get_current_class_id()
        if current_class_id:
            for student_name in self._session_generated_students:
                if student_name in self._student_data_cache:
                    next_lesson = self._student_data_cache[student_name].lesson_number + 1
                    self.config_manager.set_student_next_lesson_number(
                        current_class_id, student_name, next_lesson
                    )

        self._save_window_state()

        reply = QMessageBox.question(
            self, "确认退出",
            "是否退出程序？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    # ==================== 数据处理 ====================

    def _collect_data(self) -> CourseUnitData:
        """收集所有表单数据"""
        # 课程基本信息
        info = self.course_info_widget.get_data()
        self.current_data.lesson_number = info["lesson_number"]
        self.current_data.course_content = info["course_content"]
        self.current_data.student_name = info["student_name"]
        self.current_data.teacher_name = info["teacher_name"]
        self.current_data.class_hours = info["class_hours"]
        self.current_data.class_date = info["class_date"]

        # 课堂知识内容（从富文本编辑器获取）
        html_content = self.knowledge_editor.get_html()
        plain_content = self._clean_auto_numbering(self.knowledge_editor.get_text())

        # 从HTML中提取重点和难点词汇（带出现索引）
        highlights = self._extract_colored_words(html_content, plain_content, RichTextEditor.HIGHLIGHT_COLOR)
        difficulties = self._extract_colored_words(html_content, plain_content, RichTextEditor.DIFFICULTY_COLOR)

        self.current_data.knowledge_content = plain_content
        self.current_data.highlights = highlights
        self.current_data.difficulties = difficulties

        # 评价数据
        eval_data = self.evaluation_widget.get_data()
        from src.core.models import EvaluationLevel, OverallEvaluation, HomeworkEvaluation

        # 映射评价等级
        level_map = {
            "优": EvaluationLevel.EXCELLENT,
            "良": EvaluationLevel.GOOD,
            "中": EvaluationLevel.MEDIUM,
            "差": EvaluationLevel.POOR,
            "未体现": EvaluationLevel.NOT_SHOWN,
        }

        overall_map = {
            "优": OverallEvaluation.EXCELLENT,
            "良": OverallEvaluation.GOOD,
            "仍需努力": OverallEvaluation.NEED_EFFORT,
            "需要改进": OverallEvaluation.NEED_IMPROVEMENT,
        }

        homework_map = {
            "优": HomeworkEvaluation.EXCELLENT,
            "良": HomeworkEvaluation.GOOD,
            "中": HomeworkEvaluation.MEDIUM,
            "差": HomeworkEvaluation.POOR,
            "无": HomeworkEvaluation.NONE,
        }

        # 设置12项评价
        for key in ["logic_thinking", "content_understanding", "task_completion",
                    "listening_habit", "problem_solving", "independent_analysis",
                    "knowledge_proficiency", "imagination_creativity", "frustration_handling",
                    "learning_method", "hands_on_ability", "focus_efficiency"]:
            if eval_data.get(key) and eval_data[key] in level_map:
                setattr(self.current_data, key, level_map[eval_data[key]])

        # 总体评价
        if eval_data.get("overall_evaluation") and eval_data["overall_evaluation"] in overall_map:
            self.current_data.overall_evaluation = overall_map[eval_data["overall_evaluation"]]

        # 上次作业
        if eval_data.get("last_homework_status") and eval_data["last_homework_status"] in homework_map:
            self.current_data.last_homework_status = homework_map[eval_data["last_homework_status"]]

        # 文本
        self.current_data.additional_comments = eval_data.get("additional_comments", "")
        self.current_data.homework = eval_data.get("homework", "")
        self.current_data.other_notes = eval_data.get("other_notes", "")

        # 图片
        self.current_data.model_images = self.model_image_widget.get_images()
        self.current_data.work_images = self.work_image_widget.get_images()
        self.current_data.program_images = self.program_image_widget.get_images()
        self.current_data.vehicle_images = self.vehicle_image_widget.get_images()

        return self.current_data

    def _collect_data_to_cache(self) -> CourseUnitData:
        """收集当前表单数据到缓存对象（用于学员数据缓存）"""
        data = CourseUnitData()

        # 课程基本信息
        info = self.course_info_widget.get_data()
        data.lesson_number = info["lesson_number"]
        data.course_content = info["course_content"]
        data.student_name = info["student_name"]
        data.teacher_name = info["teacher_name"]
        data.class_hours = info["class_hours"]
        data.class_date = info["class_date"]

        # 课堂知识内容（从富文本编辑器获取）
        html_content = self.knowledge_editor.get_html()
        plain_content = self._clean_auto_numbering(self.knowledge_editor.get_text())

        # 从HTML中提取重点和难点词汇（带出现索引）
        highlights = self._extract_colored_words(html_content, plain_content, RichTextEditor.HIGHLIGHT_COLOR)
        difficulties = self._extract_colored_words(html_content, plain_content, RichTextEditor.DIFFICULTY_COLOR)

        data.knowledge_content = plain_content
        data.knowledge_html = html_content  # 保存HTML格式
        data.highlights = highlights
        data.difficulties = difficulties

        # 评价数据
        eval_data = self.evaluation_widget.get_data()
        from src.core.models import EvaluationLevel, OverallEvaluation, HomeworkEvaluation

        # 映射评价等级
        level_map = {
            "优": EvaluationLevel.EXCELLENT,
            "良": EvaluationLevel.GOOD,
            "中": EvaluationLevel.MEDIUM,
            "差": EvaluationLevel.POOR,
            "未体现": EvaluationLevel.NOT_SHOWN,
        }

        overall_map = {
            "优": OverallEvaluation.EXCELLENT,
            "良": OverallEvaluation.GOOD,
            "仍需努力": OverallEvaluation.NEED_EFFORT,
            "需要改进": OverallEvaluation.NEED_IMPROVEMENT,
        }

        homework_map = {
            "优": HomeworkEvaluation.EXCELLENT,
            "良": HomeworkEvaluation.GOOD,
            "中": HomeworkEvaluation.MEDIUM,
            "差": HomeworkEvaluation.POOR,
            "无": HomeworkEvaluation.NONE,
        }

        # 设置12项评价
        for key in ["logic_thinking", "content_understanding", "task_completion",
                    "listening_habit", "problem_solving", "independent_analysis",
                    "knowledge_proficiency", "imagination_creativity", "frustration_handling",
                    "learning_method", "hands_on_ability", "focus_efficiency"]:
            if eval_data.get(key) and eval_data[key] in level_map:
                setattr(data, key, level_map[eval_data[key]])

        # 总体评价
        if eval_data.get("overall_evaluation") and eval_data["overall_evaluation"] in overall_map:
            data.overall_evaluation = overall_map[eval_data["overall_evaluation"]]

        # 上次作业
        if eval_data.get("last_homework_status") and eval_data["last_homework_status"] in homework_map:
            data.last_homework_status = homework_map[eval_data["last_homework_status"]]

        # 文本
        data.additional_comments = eval_data.get("additional_comments", "")
        data.homework = eval_data.get("homework", "")
        data.other_notes = eval_data.get("other_notes", "")

        # 图片
        data.model_images = self.model_image_widget.get_images()
        data.work_images = self.work_image_widget.get_images()
        data.program_images = self.program_image_widget.get_images()
        data.vehicle_images = self.vehicle_image_widget.get_images()

        return data

    def _apply_cache_to_forms(self, data: CourseUnitData):
        """将缓存数据应用到表单"""
        # 阻止信号，避免加载数据时触发 data_changed
        self._loading_student_data = True

        try:
            # 基本信息
            self.course_info_widget.lesson_number.setValue(data.lesson_number)
            self.course_info_widget.course_content.setText(data.course_content)
            self.course_info_widget.student_name.setText(data.student_name)
            self.course_info_widget.teacher_name.setText(data.teacher_name)
            self.course_info_widget.class_hours.setValue(data.class_hours)
            # 注意：class_date 是 QDateTimeEdit，跳过设置（保持当前值）

            # 知识内容（优先使用HTML格式）
            if data.knowledge_html:
                self.knowledge_editor.set_html(data.knowledge_html)
            else:
                self.knowledge_editor.set_text(data.knowledge_content)

            # 评价数据
            from src.core.models import EvaluationLevel, OverallEvaluation, HomeworkEvaluation

            # 反向映射
            level_map = {
                EvaluationLevel.EXCELLENT: "优",
                EvaluationLevel.GOOD: "良",
                EvaluationLevel.MEDIUM: "中",
                EvaluationLevel.POOR: "差",
                EvaluationLevel.NOT_SHOWN: "未体现",
            }

            overall_map = {
                OverallEvaluation.EXCELLENT: "优",
                OverallEvaluation.GOOD: "良",
                OverallEvaluation.NEED_EFFORT: "仍需努力",
                OverallEvaluation.NEED_IMPROVEMENT: "需要改进",
            }

            homework_map = {
                HomeworkEvaluation.EXCELLENT: "优",
                HomeworkEvaluation.GOOD: "良",
                HomeworkEvaluation.MEDIUM: "中",
                HomeworkEvaluation.POOR: "差",
                HomeworkEvaluation.NONE: "无",
            }

            eval_data = {}
            for key in ["logic_thinking", "content_understanding", "task_completion",
                        "listening_habit", "problem_solving", "independent_analysis",
                        "knowledge_proficiency", "imagination_creativity", "frustration_handling",
                        "learning_method", "hands_on_ability", "focus_efficiency"]:
                value = getattr(data, key, EvaluationLevel.NOT_SHOWN)
                eval_data[key] = level_map.get(value, "未体现")

            eval_data["overall_evaluation"] = overall_map.get(data.overall_evaluation, "良")
            eval_data["last_homework_status"] = homework_map.get(data.last_homework_status, "无")
            eval_data["additional_comments"] = data.additional_comments
            eval_data["homework"] = data.homework
            eval_data["other_notes"] = data.other_notes

            self.evaluation_widget.set_data(eval_data)

            # 图片
            self.model_image_widget.set_images(data.model_images)
            self.work_image_widget.set_images(data.work_images)
            self.program_image_widget.set_images(data.program_images)
            self.vehicle_image_widget.set_images(data.vehicle_images)
        finally:
            self._loading_student_data = False

    def _reset_forms_for_new_student(self, student_name: str):
        """为新学员重置表单（使用默认值，并合并共享数据）"""
        # 保留系列相关数据，重置学员相关数据
        series_name, series_level = self.series_selector.get_current_series()

        # 课程内容使用"系列名(x阶)"格式
        if series_name and series_level:
            course_content = f"{series_name}（{series_level}阶）"
        else:
            course_content = series_name

        # 获取当前班级老师
        teacher_name = ""
        current_class = self.config_manager.get_current_class()
        if current_class:
            teacher_name = current_class.get("teacher", "")

        # 创建默认数据
        default_data = CourseUnitData()
        default_data.student_name = student_name
        default_data.course_content = course_content
        default_data.teacher_name = teacher_name
        # class_date 保持默认值（不覆盖，由 QDateTimeEdit 控件自己管理）

        # 加载学员上次评价数据
        current_class_id = self.class_selector.get_current_class_id()
        if current_class_id:
            last_eval = self.config_manager.get_student_last_evaluation(current_class_id, student_name)
            # 检查是否有有效的评价数据（非空且包含关键字段）
            if last_eval and any(key in last_eval for key in ["logic_thinking", "overall_evaluation"]):
                self._apply_last_evaluation_to_data(default_data, last_eval)
            else:
                # 新学员使用默认评价（全部为"优"）
                self._set_default_evaluation(default_data)

            # 作业默认值
            default_data.homework = "本次课无课堂作业"

            # 注意事项使用全局默认值
            default_data.other_notes = self.config_manager.get_default_other_notes()

            # 加载学员的课时编号（学员独立）
            next_lesson = self.config_manager.get_student_next_lesson_number(current_class_id, student_name)
            default_data.lesson_number = next_lesson

        # 合并共享数据（如果有），但不覆盖 homework 和 other_notes
        if self._class_shared_data:
            for field in self._get_active_shared_fields():
                if field not in ['homework', 'other_notes']:
                    shared_value = getattr(self._class_shared_data, field)
                    if shared_value:  # 只有非空才覆盖
                        setattr(default_data, field, shared_value)

        # 确保 student_name 保持正确（学生姓名不共享，每个学生独立）
        default_data.student_name = student_name

        self._apply_cache_to_forms(default_data)

    def _apply_last_evaluation_to_data(self, data: CourseUnitData, eval_dict: dict):
        """将存储的评价字典应用到 CourseUnitData"""
        from src.core.models import EvaluationLevel, OverallEvaluation, HomeworkEvaluation

        level_map = {
            "优": EvaluationLevel.EXCELLENT,
            "良": EvaluationLevel.GOOD,
            "中": EvaluationLevel.MEDIUM,
            "差": EvaluationLevel.POOR,
            "未体现": EvaluationLevel.NOT_SHOWN,
        }

        overall_map = {
            "优": OverallEvaluation.EXCELLENT,
            "良": OverallEvaluation.GOOD,
            "仍需努力": OverallEvaluation.NEED_EFFORT,
            "需要改进": OverallEvaluation.NEED_IMPROVEMENT,
        }

        homework_map = {
            "优": HomeworkEvaluation.EXCELLENT,
            "良": HomeworkEvaluation.GOOD,
            "中": HomeworkEvaluation.MEDIUM,
            "差": HomeworkEvaluation.POOR,
            "无": HomeworkEvaluation.NONE,
        }

        # 12项评价
        for key in ["logic_thinking", "content_understanding", "task_completion",
                    "listening_habit", "problem_solving", "independent_analysis",
                    "knowledge_proficiency", "imagination_creativity", "frustration_handling",
                    "learning_method", "hands_on_ability", "focus_efficiency"]:
            if key in eval_dict and eval_dict[key] in level_map:
                setattr(data, key, level_map[eval_dict[key]])

        # 总体评价
        if "overall_evaluation" in eval_dict and eval_dict["overall_evaluation"] in overall_map:
            data.overall_evaluation = overall_map[eval_dict["overall_evaluation"]]

        # 上次作业
        if "last_homework_status" in eval_dict and eval_dict["last_homework_status"] in homework_map:
            data.last_homework_status = homework_map[eval_dict["last_homework_status"]]

        # 补充说明
        if "additional_comments" in eval_dict:
            data.additional_comments = eval_dict["additional_comments"]

    def _set_default_evaluation(self, data: CourseUnitData):
        """设置新学员的默认评价（全部为"优"）"""
        from src.core.models import EvaluationLevel, OverallEvaluation, HomeworkEvaluation

        # 12项评价默认为"优"
        for key in ["logic_thinking", "content_understanding", "task_completion",
                    "listening_habit", "problem_solving", "independent_analysis",
                    "knowledge_proficiency", "imagination_creativity", "frustration_handling",
                    "learning_method", "hands_on_ability", "focus_efficiency"]:
            setattr(data, key, EvaluationLevel.EXCELLENT)

        # 总体评价默认为"优"
        data.overall_evaluation = OverallEvaluation.EXCELLENT

        # 上次作业默认为"无"
        data.last_homework_status = HomeworkEvaluation.NONE

    def _save_current_student_data(self):
        """保存当前学员数据到缓存和持久化存储"""
        if self._current_student_name:
            data = self._collect_data_to_cache()
            self._student_data_cache[self._current_student_name] = data

            # 保存学员评价和课时编号到持久化存储
            current_class_id = self.class_selector.get_current_class_id()
            if current_class_id:
                eval_dict = self._extract_evaluation_from_data(data)
                self.config_manager.save_student_last_evaluation(
                    current_class_id,
                    self._current_student_name,
                    eval_dict
                )

    def _extract_evaluation_from_data(self, data: CourseUnitData) -> dict:
        """从 CourseUnitData 提取评价字典用于持久化"""
        from src.core.models import EvaluationLevel, OverallEvaluation, HomeworkEvaluation

        level_map = {
            EvaluationLevel.EXCELLENT: "优",
            EvaluationLevel.GOOD: "良",
            EvaluationLevel.MEDIUM: "中",
            EvaluationLevel.POOR: "差",
            EvaluationLevel.NOT_SHOWN: "未体现",
        }

        overall_map = {
            OverallEvaluation.EXCELLENT: "优",
            OverallEvaluation.GOOD: "良",
            OverallEvaluation.NEED_EFFORT: "仍需努力",
            OverallEvaluation.NEED_IMPROVEMENT: "需要改进",
        }

        homework_map = {
            HomeworkEvaluation.EXCELLENT: "优",
            HomeworkEvaluation.GOOD: "良",
            HomeworkEvaluation.MEDIUM: "中",
            HomeworkEvaluation.POOR: "差",
            HomeworkEvaluation.NONE: "无",
        }

        eval_dict = {}

        # 12项评价
        for key in ["logic_thinking", "content_understanding", "task_completion",
                    "listening_habit", "problem_solving", "independent_analysis",
                    "knowledge_proficiency", "imagination_creativity", "frustration_handling",
                    "learning_method", "hands_on_ability", "focus_efficiency"]:
            value = getattr(data, key, EvaluationLevel.NOT_SHOWN)
            eval_dict[key] = level_map.get(value, "未体现")

        # 总体评价
        eval_dict["overall_evaluation"] = overall_map.get(data.overall_evaluation, "良")

        # 上次作业
        eval_dict["last_homework_status"] = homework_map.get(data.last_homework_status, "无")

        # 补充说明
        eval_dict["additional_comments"] = data.additional_comments

        return eval_dict

    def _update_shared_data_from_forms(self):
        """从当前表单更新共享数据"""
        if self._loading_student_data or self._syncing_shared_data:
            return

        if not self._class_shared_data:
            self._class_shared_data = CourseUnitData()

        self._syncing_shared_data = True
        try:
            # 课程内容、授课教师（课时编号不再同步，改为学员独立）
            info = self.course_info_widget.get_data()
            self._class_shared_data.course_content = info["course_content"]
            self._class_shared_data.teacher_name = info["teacher_name"]

            # 知识内容
            html_content = self.knowledge_editor.get_html()
            plain_content = self._clean_auto_numbering(self.knowledge_editor.get_text())
            highlights = self._extract_colored_words(html_content, plain_content, RichTextEditor.HIGHLIGHT_COLOR)
            difficulties = self._extract_colored_words(html_content, plain_content, RichTextEditor.DIFFICULTY_COLOR)

            self._class_shared_data.knowledge_content = plain_content
            self._class_shared_data.knowledge_html = html_content
            self._class_shared_data.highlights = highlights
            self._class_shared_data.difficulties = difficulties

            # 评价组件中的共享字段
            eval_data = self.evaluation_widget.get_data()
            self._class_shared_data.homework = eval_data.get("homework", "")
            self._class_shared_data.other_notes = eval_data.get("other_notes", "")

            # 保存注意事项到全局默认值
            other_notes = eval_data.get("other_notes", "")
            if other_notes:
                self.config_manager.save_default_other_notes(other_notes)

            # 图片（只同步启用了同步的字段，work_images 始终独立）
            if self._image_sync_states['model_images']:
                self._class_shared_data.model_images = self.model_image_widget.get_images()
            if self._image_sync_states['program_images']:
                self._class_shared_data.program_images = self.program_image_widget.get_images()
            if self._image_sync_states['vehicle_images']:
                self._class_shared_data.vehicle_images = self.vehicle_image_widget.get_images()
        finally:
            self._syncing_shared_data = False

    def _copy_course_data(self, source: CourseUnitData) -> CourseUnitData:
        """创建 CourseUnitData 的副本，避免直接修改缓存"""
        import copy
        dest = CourseUnitData()
        # 复制基础字段
        for field in ['lesson_number', 'course_content', 'student_name', 'teacher_name',
                      'class_hours', 'class_date', 'knowledge_content', 'knowledge_html',
                      'highlights', 'difficulties', 'homework', 'other_notes',
                      'additional_comments', 'model_images', 'work_images',
                      'program_images', 'vehicle_images']:
            if hasattr(source, field):
                value = getattr(source, field)
                setattr(dest, field, copy.deepcopy(value) if isinstance(value, (list, dict)) else value)
        # 复制评价字段
        for key in ["logic_thinking", "content_understanding", "task_completion",
                    "listening_habit", "problem_solving", "independent_analysis",
                    "knowledge_proficiency", "imagination_creativity", "frustration_handling",
                    "learning_method", "hands_on_ability", "focus_efficiency"]:
            setattr(dest, key, getattr(source, key))
        dest.overall_evaluation = source.overall_evaluation
        dest.last_homework_status = source.last_homework_status
        return dest

    def _create_student_data_from_persisted(self, student_name: str) -> CourseUnitData:
        """从持久化加载学员数据（用于合并同步数据）"""
        series_name, series_level = self.series_selector.get_current_series()
        if series_name and series_level:
            course_content = f"{series_name}（{series_level}阶）"
        else:
            course_content = series_name

        teacher_name = ""
        current_class = self.config_manager.get_current_class()
        if current_class:
            teacher_name = current_class.get("teacher", "")

        data = CourseUnitData()
        data.student_name = student_name
        data.course_content = course_content
        data.teacher_name = teacher_name

        # 加载持久化评价数据
        current_class_id = self.class_selector.get_current_class_id()
        if current_class_id:
            last_eval = self.config_manager.get_student_last_evaluation(current_class_id, student_name)
            # 评价相关字段列表（任一字段存在即认为有历史评价）
            evaluation_keys = [
                "logic_thinking", "content_understanding", "task_completion",
                "listening_habit", "problem_solving", "independent_analysis",
                "knowledge_proficiency", "imagination_creativity", "frustration_handling",
                "learning_method", "hands_on_ability", "focus_efficiency",
                "overall_evaluation", "last_homework_status"
            ]
            if last_eval and any(key in last_eval for key in evaluation_keys):
                self._apply_last_evaluation_to_data(data, last_eval)
            else:
                self._set_default_evaluation(data)

            data.homework = "本次课无课堂作业"
            data.other_notes = self.config_manager.get_default_other_notes()

            # 加载学员的课时编号（学员独立）
            next_lesson = self.config_manager.get_student_next_lesson_number(current_class_id, student_name)
            data.lesson_number = next_lesson

        return data

    def _load_student_data(self, student_name: str):
        """从缓存加载学员数据到表单（合并共享数据）"""
        cached_comments = None  # 保存同步的补充说明

        if student_name in self._student_data_cache:
            cached_data = self._student_data_cache[student_name]
            # 检查缓存数据是否完整（是否包含评价数据）
            # 使用 _synced_comments_cache 标记判断：如果在该集合中，说明是"仅同步补充说明"的不完整缓存
            # 不应该通过评价的具体值来判断，因为用户可能确实选择了 NOT_SHOWN 和 GOOD
            is_incomplete_sync_cache = student_name in self._synced_comments_cache

            if not is_incomplete_sync_cache:
                # 创建副本，避免直接修改缓存
                independent_data = self._copy_course_data(cached_data)
            else:
                # 保存同步的补充说明（如果有）
                if cached_data.additional_comments:
                    cached_comments = cached_data.additional_comments
                # 缓存数据不完整，从持久化加载
                independent_data = None
        else:
            independent_data = None

        # 如果没有完整的缓存数据，从持久化加载
        if independent_data is None:
            independent_data = self._create_student_data_from_persisted(student_name)

            # 合并缓存的补充说明（如果有）
            if cached_comments:
                independent_data.additional_comments = cached_comments
                # 更新缓存为完整数据
                self._student_data_cache[student_name] = self._copy_course_data(independent_data)
                # 清除同步标记（数据已完整）
                self._synced_comments_cache.discard(student_name)

        # 如果有缓存数据且有共享数据，合并共享字段到副本
        if independent_data and self._class_shared_data:
            for field in self._get_active_shared_fields():
                if field == 'homework':
                    # 只有当缓存中没有有效值时才使用默认值
                    if not independent_data.homework:
                        independent_data.homework = "本次课无课堂作业"
                elif field == 'other_notes':
                    # 只有当缓存中没有有效值时才使用默认值
                    if not independent_data.other_notes:
                        independent_data.other_notes = self.config_manager.get_default_other_notes()
                else:
                    # 其他字段：只有当共享数据非空时才覆盖
                    shared_value = getattr(self._class_shared_data, field)
                    if shared_value:  # 非空值才覆盖
                        setattr(independent_data, field, shared_value)

        # 注意：课时编号已从缓存加载，无需再从配置覆盖
        # _save_current_student_data 已将课时编号持久化到配置
        # 只有新学员（不在缓存中）才会在后续逻辑中从配置加载

        if independent_data:
            # 确保 student_name 保持正确（学生姓名不共享，每个学生独立）
            independent_data.student_name = student_name
            self._apply_cache_to_forms(independent_data)

            # 记录会话初始值（仅首次加载时）
            if student_name not in self._session_initial_comments:
                self._session_initial_comments[student_name] = independent_data.additional_comments.strip()
        else:
            self._reset_forms_for_new_student(student_name)
            # 记录会话初始值（仅首次加载时）- 新学员初始值为空
            if student_name not in self._session_initial_comments:
                self._session_initial_comments[student_name] = ""

    def _clean_auto_numbering(self, text: str) -> str:
        """
        去除每行开头的数字编号（如 1. 2. 3.）

        用户粘贴课堂知识内容时，文本可能已带有编号。
        PPT生成时通过 buAutoNum 自动添加编号，导致编号重复。
        此方法预处理文本，去除已存在的编号。

        Args:
            text: 原始文本

        Returns:
            清理编号后的文本
        """
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # 匹配行首的数字编号模式：1. 2. 3. 等
            cleaned = re.sub(r'^(\d+)\.\s*', '', line.strip())
            cleaned_lines.append(cleaned)
        return '\n'.join(cleaned_lines)

    def _extract_colored_words(self, html: str, plain_text: str, target_color) -> List:
        """
        从HTML中提取指定颜色的文字，并计算其在纯文本中的出现索引

        核心思路（改进版）：
        1. 解析HTML，重建与toPlainText()一致的纯文本
        2. 记录每个HTML文本节点在重建文本中的位置范围
        3. 找到着色span对应的文本节点
        4. 根据位置范围确定该词汇在纯文本中的位置
        5. 计算该位置是词汇的第几次出现

        Args:
            html: HTML文本
            plain_text: 纯文本内容（由toPlainText()生成）
            target_color: 目标颜色（QColor对象）

        Returns:
            [(词汇, 出现索引), ...]
        """
        import re

        markers = []
        target_hex = target_color.name().lower()

        # 第一步：解析HTML并建立文本位置映射
        # 存储格式: [(span在重建文本中的起始位置, span结束位置, span文本, span颜色), ...]
        colored_spans = []

        # 重建的纯文本（应该与toPlainText()输出一致）
        rebuilt_text = ""
        current_pos = 0

        # 使用正则表达式解析Qt的HTML格式
        # Qt使用<p>标签表示段落，段落之间用换行符分隔
        # 段落内的span标签表示格式化文本

        # 首先按<p>标签分割
        p_pattern = r'<p[^>]*>(.*?)</p>'

        # 匹配所有带颜色的span标签
        # 模式：匹配普通文本和带颜色的span
        span_pattern = r'<span[^>]*style\s*=\s*"[^"]*color\s*:\s*#([0-9a-fA-F]{6})[^"]*"[^>]*>([^<]+)</span>'

        # 遍历所有段落
        paragraphs = re.findall(p_pattern, html, re.DOTALL)

        for para_idx, para_content in enumerate(paragraphs):
            # 段落之间的分隔
            if para_idx > 0:
                rebuilt_text += '\n'
                current_pos += 1

            # 在段落内，找到所有带颜色的span和普通文本
            # 使用迭代方式处理段落内容
            para_text_only = re.sub(r'<[^>]+>', '', para_content)  # 去除标签后的纯文本

            # 查找段落中所有着色的span
            for span_match in re.finditer(span_pattern, para_content, re.IGNORECASE):
                span_html_start = span_match.start()
                color_hex = '#' + span_match.group(1).lower()
                span_text = span_match.group(2)

                # 计算这个span在段落纯文本中的位置
                # 需要计算span开始之前有多少纯文本字符
                text_before_span = re.sub(r'<[^>]+>', '', para_content[:span_html_start])
                span_start_in_para = len(text_before_span)

                # 在重建文本中的绝对位置
                abs_start = current_pos + span_start_in_para
                abs_end = abs_start + len(span_text)

                # 记录着色span信息
                if color_hex == target_hex:
                    colored_spans.append((abs_start, abs_end, span_text, color_hex))

            # 更新重建文本
            rebuilt_text += para_text_only
            current_pos += len(para_text_only)

        # 第二步：对于每个着色span，计算其出现索引
        for abs_start, abs_end, span_text, color_hex in colored_spans:
            word = span_text.strip()
            if not word:
                continue

            # 在plain_text中找到abs_start位置对应的词汇出现次数
            # 关键：span_start应该在词汇的某个出现位置附近
            # 我们需要找到：在abs_start位置或之前，该词汇最后一次出现是第几次

            occurrence = 0
            search_pos = 0

            while True:
                found_pos = plain_text.find(word, search_pos)
                if found_pos == -1:
                    break
                # 检查找到的位置是否在span范围内或之前
                # 由于重建文本可能与plain_text有细微差异，使用容错匹配
                if found_pos <= abs_end:  # 使用abs_end作为上限，增加容错性
                    # 验证：如果found_pos在abs_start附近（前后容差），这可能是我们要找的
                    occurrence += 1
                    # 如果找到的位置与span起始位置接近，这很可能就是正确的出现
                    if found_pos <= abs_start < found_pos + len(word):
                        break  # 找到了正确的出现
                    search_pos = found_pos + len(word)
                else:
                    break

            # 如果没有找到精确匹配，使用计算出的occurrence
            if occurrence == 0:
                # 重新计算：找到所有在abs_start之前或等于abs_start的出现
                occurrence = 0
                search_pos = 0
                while True:
                    found_pos = plain_text.find(word, search_pos)
                    if found_pos == -1 or found_pos > abs_start:
                        break
                    occurrence += 1
                    search_pos = found_pos + len(word)

            if occurrence > 0:
                markers.append((word, occurrence))

        return markers

    def _on_data_changed(self):
        """数据改变回调"""
        # 如果正在加载学员数据或同步共享数据，跳过
        if self._loading_student_data or self._syncing_shared_data:
            return

        # 更新共享数据
        self._update_shared_data_from_forms()

        # 检测补充说明变化并触发同步
        self._check_and_sync_additional_comments()

        self._collect_data()
        self.data_changed.emit()

    def _on_layout_changed(self, config: dict):
        """布局配置改变"""
        # 保存到当前班级（如果有选中的班级）
        current_class_id = self.class_selector.get_current_class_id()
        if current_class_id:
            self.config_manager.set_class_layout_config(current_class_id, config)
        else:
            # 没有选中班级时，保存为全局配置
            self.config_manager.set_layout_config(config)
        # 联动：更新图片上传组件可见性
        self._update_image_widget_visibility(config)

    def _update_image_widget_visibility(self, config: dict):
        """根据布局配置更新图片上传组件的可见性"""
        self.model_image_widget.setVisible(config.get("include_model_display", True))
        self.work_image_widget.setVisible(config.get("include_work_display", True))
        self.program_image_widget.setVisible(config.get("include_program_display", False))
        self.vehicle_image_widget.setVisible(config.get("include_vehicle_display", False))

    def _on_images_changed(self, images: list):
        """图片改变回调"""
        # 如果正在加载学员数据或同步共享数据，跳过
        if self._loading_student_data or self._syncing_shared_data:
            return

        # 更新共享数据中的图片
        self._update_shared_data_from_forms()

        self._collect_data()

    def _on_model_image_sync_toggled(self, enabled: bool):
        """模型图片同步状态切换"""
        self._image_sync_states['model_images'] = enabled
        self._on_image_sync_state_changed('model_images', enabled)

    def _on_program_image_sync_toggled(self, enabled: bool):
        """程序图片同步状态切换"""
        self._image_sync_states['program_images'] = enabled
        self._on_image_sync_state_changed('program_images', enabled)

    def _on_vehicle_image_sync_toggled(self, enabled: bool):
        """车辆图片同步状态切换"""
        self._image_sync_states['vehicle_images'] = enabled
        self._on_image_sync_state_changed('vehicle_images', enabled)

    def _on_image_sync_state_changed(self, field: str, enabled: bool):
        """处理图片同步状态变化"""
        if enabled:
            # 切换为同步模式：将当前学员的图片写入共享数据
            if field == 'model_images':
                images = self.model_image_widget.get_images()
            elif field == 'program_images':
                images = self.program_image_widget.get_images()
            elif field == 'vehicle_images':
                images = self.vehicle_image_widget.get_images()
            else:
                return

            if self._class_shared_data:
                setattr(self._class_shared_data, field, images)
        # 切换为独立模式：无需特殊处理，数据已在学员缓存中

    def _get_active_shared_fields(self) -> List[str]:
        """获取当前有效的共享字段列表（包含启用同步的图片字段）"""
        base_fields = list(self._SHARED_FIELDS)
        # 添加启用同步的图片字段
        if self._image_sync_states.get('model_images', True):
            base_fields.append('model_images')
        if self._image_sync_states.get('program_images', True):
            base_fields.append('program_images')
        if self._image_sync_states.get('vehicle_images', True):
            base_fields.append('vehicle_images')
        return base_fields

    def _on_series_changed(self, series_name: str, series_level: int):
        """用户手动切换系列 - 自动更新课程内容并保存关联"""
        # 更新课程内容字段为"系列名(x阶)"格式
        if series_name and series_level:
            course_content = f"{series_name}（{series_level}阶）"
        else:
            course_content = series_name
        self.course_info_widget.course_content.setText(course_content)

        # 保存班级与系列的关联
        current_class_id = self.class_selector.get_current_class_id()
        if current_class_id:
            series_list = self.config_manager.get_course_series()
            for i, s in enumerate(series_list):
                if s.get("name") == series_name and s.get("level") == series_level:
                    self.config_manager.set_class_series_index(current_class_id, i)
                    break

        self._on_data_changed()

    def _on_class_series_changed(self, series_index: int):
        """班级切换时自动切换到关联的系列"""
        self.series_selector.set_series_silently(series_index)
        # 更新课程内容显示
        series_name, series_level = self.series_selector.get_current_series()
        if series_name and series_level:
            course_content = f"{series_name}（{series_level}阶）"
        else:
            course_content = series_name
        self.course_info_widget.course_content.setText(course_content)

    def _on_class_changed(self, class_id: str):
        """班级选择改变回调 - 加载该班级的学员"""
        # 保存当前学员数据
        self._save_current_student_data()

        # 更新当前班级ID
        self._current_class_id = class_id

        # 切换班级清空缓存和共享数据
        self._student_data_cache.clear()
        self._current_student_name = ""
        self._class_shared_data = CourseUnitData()  # 初始化新的共享数据

        # 重置图片同步状态为默认同步
        self._image_sync_states = {
            'model_images': True,
            'program_images': True,
            'vehicle_images': True,
        }
        # 更新UI按钮状态
        self.model_image_widget.set_sync_enabled(True)
        self.program_image_widget.set_sync_enabled(True)
        self.vehicle_image_widget.set_sync_enabled(True)

        # 重置补充说明同步状态
        self._comments_sync_source = ""
        self._comments_sync_locked = False
        self._comments_sync_content = ""
        self._synced_comments_cache.clear()  # 清空同步标记

        # 切换班级时清空会话初始值（用于检查补充说明是否修改）
        self._session_initial_comments.clear()

        # 加载学员到管理器和标签栏
        self.student_manager.load_students(class_id)
        students = self.config_manager.get_students_by_class(class_id)
        self.student_tab_bar.load_students(students)

        # 自动填充上课时间
        current_class = self.config_manager.get_current_class()
        if current_class:
            class_name = current_class.get("name", "")
            time_info = ClassSelectorWidget.parse_class_name(class_name)
            if time_info:
                self.course_info_widget.set_class_time(
                    time_info["weekday"],
                    time_info["hour"],
                    time_info["minute"]
                )

        # 加载班级的母版配置
        if class_id:
            layout_config = self.config_manager.get_class_layout_config(class_id)
            if layout_config:
                self.layout_selector.set_config(layout_config)
                self._update_image_widget_visibility(layout_config)
            else:
                # 使用全局默认配置
                default_config = self.config_manager.get_layout_config()
                self.layout_selector.set_config(default_config)
                self._update_image_widget_visibility(default_config)

    def _on_teacher_changed(self, teacher_name: str):
        """班级老师改变回调 - 填充教师姓名到表单"""
        if teacher_name:
            self.course_info_widget.teacher_name.setText(teacher_name)
            self._on_data_changed()

    def _on_student_selected(self, student_name: str):
        """学员选择回调 - 填充学生姓名到表单"""
        # 如果学员在标签栏中，同步标签栏选择并触发数据切换
        if student_name in self.student_tab_bar._buttons:
            # 直接触发学员切换（保存当前数据，加载新数据）
            self._on_student_tab_changed(student_name)
            # 同步标签栏选中状态
            self.student_tab_bar.set_current_student(student_name)
        else:
            # 学员不在标签栏中，直接填充姓名
            self.course_info_widget.student_name.setText(student_name)
            self._current_student_name = student_name
            self._on_data_changed()

    def _on_students_changed(self):
        """学员列表变化回调 - 刷新标签栏"""
        class_id = self.class_selector.get_current_class_id()
        if class_id:
            students = self.config_manager.get_students_by_class(class_id)
            self.student_tab_bar.load_students(students)

    def _check_and_sync_additional_comments(self):
        """检测补充说明变化并执行同步"""
        if self._loading_student_data or self._syncing_shared_data:
            return

        current_comments = self.evaluation_widget.additional_comments.toPlainText()
        current_student = self._current_student_name

        if not current_student:
            return

        # 检测内容是否变化
        if current_comments == self._comments_sync_content:
            return

        # 判断同步状态
        if not self._comments_sync_source:
            # 首位填写者：记录来源并同步
            self._comments_sync_source = current_student
            self._comments_sync_content = current_comments
            self._sync_comments_to_all_students(current_student, current_comments)
        elif self._comments_sync_source == current_student and not self._comments_sync_locked:
            # 首位同学继续修改：继续同步
            self._comments_sync_content = current_comments
            self._sync_comments_to_all_students(current_student, current_comments)
        elif current_student != self._comments_sync_source:
            # 其他同学修改：锁定同步
            self._comments_sync_locked = True

    def _sync_comments_to_all_students(self, source_student: str, source_comments: str):
        """将补充说明同步给所有其他同学（带名字替换）"""
        class_id = self.class_selector.get_current_class_id()
        if not class_id:
            return

        students = self.config_manager.get_students_by_class(class_id)
        source_info = self._get_student_info(students, source_student)

        for student in students:
            target_name = student.get("name", "")
            if target_name == source_student:
                continue  # 跳过源学员

            target_nickname = student.get("nickname", "")
            # 替换名字
            target_comments = self._replace_student_names(
                source_comments,
                source_info,
                {"name": target_name, "nickname": target_nickname}
            )

            # 更新缓存
            if target_name in self._student_data_cache:
                self._student_data_cache[target_name].additional_comments = target_comments
            else:
                # 创建新缓存并标记为同步数据
                new_data = CourseUnitData()
                new_data.additional_comments = target_comments
                self._student_data_cache[target_name] = new_data
                self._synced_comments_cache.add(target_name)  # 添加标记

            # 关键修复：为被同步的同学设置正确的初始值
            # 如果该同学还未记录初始值，从持久化获取同步前的值
            if target_name not in self._session_initial_comments:
                last_eval = self.config_manager.get_student_last_evaluation(class_id, target_name)
                initial_comments = last_eval.get("additional_comments", "").strip() if last_eval else ""
                self._session_initial_comments[target_name] = initial_comments

    def _get_student_info(self, students: list, name: str) -> dict:
        """获取学员信息"""
        for s in students:
            if s.get("name") == name:
                return s
        return {"name": name, "nickname": ""}

    def _replace_student_names(self, text: str, source: dict, target: dict) -> str:
        """
        替换文本中的学员名字

        规则：
        1. 优先匹配大名，替换为目标大名
        2. 小名替换时，跳过紧跟在大名后面的小名（已被大名替换覆盖）
        3. 独立出现的小名需要替换
        """
        source_name = source.get("name", "")
        source_nickname = source.get("nickname", "")
        target_name = target.get("name", "")
        target_nickname = target.get("nickname", "")

        if not text:
            return text

        if not source_name and not source_nickname:
            return text

        # 如果没有小名，直接替换大名
        if not source_nickname:
            return text.replace(source_name, target_name) if source_name else text

        # 检查小名是否是大名的后缀
        nickname_is_suffix = (
            source_name and
            len(source_name) >= 2 and
            source_name.endswith(source_nickname)
        )

        if not nickname_is_suffix:
            # 小名不是大名后缀，独立替换
            result = text
            if source_name:
                result = result.replace(source_name, target_name)
            result = result.replace(source_nickname, target_nickname)
            return result

        # 小名是大名后缀的情况，需要智能处理
        # 1. 找出所有大名的位置（结束位置）
        # 2. 找出所有小名的位置（起始位置）
        # 3. 只替换不紧跟在大名后面的小名

        # 记录大名结束位置
        name_end_positions = set()
        pos = 0
        while True:
            pos = text.find(source_name, pos)
            if pos == -1:
                break
            name_end_positions.add(pos + len(source_name))
            pos += 1

        # 找出需要替换的小名位置（不紧跟在大名后面的）
        # 小名紧跟大名后 => 小名起始位置 == 大名结束位置 - len(source_nickname) + len(source_nickname)
        # 即小名起始位置 == 大名结束位置 - len(source_nickname)
        # 但更简单：小名起始位置 + len(source_nickname) == 大名结束位置时，小名在大名内

        # 实际上：如果小名是大名后2字，那么小名起始位置 = 大名起始位置 + len(大名) - len(小名)
        # 大名结束位置 = 大名起始位置 + len(大名)
        # 所以：小名起始位置 = 大名结束位置 - len(小名)

        name_start_positions = set()
        pos = 0
        while True:
            pos = text.find(source_name, pos)
            if pos == -1:
                break
            name_start_positions.add(pos)
            pos += 1

        # 计算小名在大名内的起始位置（这些位置的小名不需要替换）
        nickname_inside_positions = set()
        for name_start in name_start_positions:
            nickname_start = name_start + len(source_name) - len(source_nickname)
            nickname_inside_positions.add(nickname_start)

        # 找出所有小名位置，替换不在大名内的
        result = []
        pos = 0
        while pos < len(text):
            # 检查当前位置是否是大名的起始
            if pos in name_start_positions:
                # 替换大名
                result.append(target_name)
                pos += len(source_name)
            # 检查当前位置是否是小名的起始
            elif text[pos:pos + len(source_nickname)] == source_nickname:
                if pos in nickname_inside_positions:
                    # 小名在大名内，已经被大名替换覆盖，跳过
                    # 但这里我们已经处理了大名，所以不应该走到这里
                    # 安全起见，保留原文
                    result.append(source_nickname)
                else:
                    # 独立的小名，替换
                    result.append(target_nickname)
                pos += len(source_nickname)
            else:
                result.append(text[pos])
                pos += 1

        return ''.join(result)

    def _force_sync_comments(self):
        """强制同步补充说明给所有同学"""
        current_comments = self.evaluation_widget.additional_comments.toPlainText()
        current_student = self._current_student_name

        if not current_student or not current_comments:
            QMessageBox.information(self, "提示", "请先输入补充说明内容")
            return

        class_id = self.class_selector.get_current_class_id()
        if class_id:
            students = self.config_manager.get_students_by_class(class_id)
            if len(students) <= 1:
                QMessageBox.information(self, "提示", "班级只有一位同学，无需同步")
                return

            reply = QMessageBox.question(
                self, "确认同步",
                "确定要将当前补充说明同步给班级所有其他同学吗？\n\n系统会自动替换名字。",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # 执行强制同步（不更新锁定状态）
                self._sync_comments_to_all_students(current_student, current_comments)

                # 更新同步源（成为新的首位）
                self._comments_sync_source = current_student
                self._comments_sync_locked = False
                self._comments_sync_content = current_comments

                # 清除所有同步标记（强制同步后数据是完整的）
                self._synced_comments_cache.clear()

                QMessageBox.information(self, "成功", f"已同步给 {len(students) - 1} 位同学")

    def _on_student_tab_changed(self, student_name: str):
        """学员标签切换回调"""
        # 保存当前学员数据
        self._save_current_student_data()

        # 更新当前学员
        self._current_student_name = student_name

        # 加载新学员数据
        self._load_student_data(student_name)

        # 确保表单中的学生姓名正确（防止被信号处理覆盖）
        if student_name:
            self.course_info_widget.student_name.setText(student_name)

        # 更新 current_data 引用
        self.current_data = self._collect_data_to_cache()

    # ==================== 菜单动作处理 ====================

    def _on_new(self):
        """新建课程反馈"""
        reply = QMessageBox.question(
            self, "确认新建",
            "确定要新建吗？当前未保存的数据将丢失。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.current_data = CourseUnitData()
            # 清空学员数据缓存
            self._student_data_cache.clear()
            self._current_student_name = ""
            self.student_tab_bar.clear_selection()
            # 清空表单
            self.course_info_widget.clear()
            self.knowledge_editor.clear()
            self.evaluation_widget.clear()
            self.model_image_widget.clear_images()
            self.work_image_widget.clear_images()
            self.program_image_widget.clear_images()
            self.vehicle_image_widget.clear_images()
            self.update_status("已创建新的课程反馈")

    def _on_open(self):
        """打开已保存的数据"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开课程数据", "", "JSON文件 (*.json);;所有文件 (*)"
        )

        if file_path:
            self.update_status(f"已打开: {Path(file_path).name}")

    def _on_save(self):
        """保存当前数据"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存课程数据",
            f"{self.current_data.student_name}_课程数据.json",
            "JSON文件 (*.json);;所有文件 (*)"
        )

        if file_path:
            self.update_status(f"已保存: {Path(file_path).name}")

    def _on_import_excel(self):
        """导入Excel — 使用 ExcelImportDialog 选择数据"""
        from src.ui.dialogs.excel_import_dialog import ExcelImportDialog
        dialog = ExcelImportDialog(parent=self)
        if dialog.exec_() == dialog.Accepted:
            data_list = dialog.get_selected_data()
            if data_list:
                # 事件追踪：Excel 导入
                tracker = getattr(self, '_event_tracker', None)
                if tracker:
                    tracker.track_import(student_count=len(data_list))
                self.update_status(f"已导入 {len(data_list)} 条数据")

    def _on_export_config(self):
        """导出配置到文件（选择性）"""
        self._save_current_student_data()

        dialog = ConfigTransferDialog(
            ConfigTransferDialog.MODE_EXPORT,
            self.config_manager,
            parent=self
        )
        if dialog.exec_() != QDialog.Accepted:
            return

        selection = dialog.get_selection()

        default_name = "PPTGenerator_配置备份.json"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出配置", default_name,
            "JSON配置文件 (*.json);;所有文件 (*)"
        )

        if not file_path:
            return

        if self.config_manager.export_config_selective(file_path, selection):
            class_count = len(selection["selected_class_ids"])
            QMessageBox.information(
                self, "导出成功",
                f"已导出 {class_count} 个班级的配置到:\n{file_path}\n\n"
                "将此文件复制到新电脑后，通过菜单\n"
                "\"文件 → 导入配置\" 即可恢复。"
            )
            self.update_status(f"配置已导出: {Path(file_path).name}")
        else:
            QMessageBox.critical(self, "导出失败", "导出配置时发生错误。")

    def _on_import_config(self):
        """从文件导入配置（选择性）"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入配置", "",
            "JSON配置文件 (*.json);;所有文件 (*)"
        )

        if not file_path:
            return

        # 预读文件内容
        import_data = self.config_manager.read_config_file(file_path)
        if not import_data:
            QMessageBox.critical(
                self, "导入失败",
                "无法读取配置文件。\n请确认是有效的 PPTGenerator 配置文件。"
            )
            return

        dialog = ConfigTransferDialog(
            ConfigTransferDialog.MODE_IMPORT,
            self.config_manager,
            import_file_path=file_path,
            parent=self
        )
        if dialog.exec_() != QDialog.Accepted:
            return

        selection = dialog.get_selection()

        if self.config_manager.import_config_selective(file_path, selection):
            self._reload_after_config_import()
            class_count = len(selection["selected_class_ids"])
            QMessageBox.information(
                self, "导入成功",
                f"已成功导入 {class_count} 个班级的配置！"
            )
            self.update_status("配置导入成功")
        else:
            QMessageBox.critical(self, "导入失败", "导入配置时发生错误。")

    def _reload_after_config_import(self):
        """配置导入后重新加载界面"""
        # 清空学员数据缓存
        self._student_data_cache.clear()
        self._current_student_name = ""
        self._class_shared_data = CourseUnitData()

        # 重置图片和补充说明同步状态
        self._image_sync_states = {
            'model_images': True,
            'program_images': True,
            'vehicle_images': True,
        }
        self._comments_sync_source = ""
        self._comments_sync_locked = False
        self._comments_sync_content = ""
        self._synced_comments_cache.clear()
        self._session_initial_comments.clear()

        # 刷新系列选择器
        self.series_selector.refresh_series_list()

        # 刷新班级选择器
        self.class_selector.refresh_class_list()

        # 重新加载当前班级数据
        self._init_default_values()

        # 应用主题
        saved_theme = self.config_manager.get_theme()
        ThemeManager.instance().set_theme(saved_theme)

        # 清空表单
        self.course_info_widget.clear()
        self.knowledge_editor.clear()
        self.evaluation_widget.clear()
        self.model_image_widget.clear_images()
        self.work_image_widget.clear_images()
        self.program_image_widget.clear_images()
        self.vehicle_image_widget.clear_images()
        self.student_tab_bar.clear_selection()

    def _check_content_before_generation(self, is_batch: bool = False) -> tuple[bool, list[str]]:
        """
        生成前内容检查

        Args:
            is_batch: 是否批量生成

        Returns:
            (should_continue, issues): 是否通过检查, 问题列表
        """
        issues = []

        # 收集数据
        self._collect_data()
        data = self.current_data

        # 检查1: 课堂知识内容为空
        if not data.knowledge_content.strip():
            issues.append("课堂知识内容为空")

        # 检查2: 无重点标记
        if len(data.highlights) == 0:
            issues.append("未标记重点词汇")

        # 检查3: 无难点标记
        if len(data.difficulties) == 0:
            issues.append("未标记难点词汇")

        # 检查4: 勾选的图片类型未上传图片
        layout_config = self.layout_selector.get_config()
        model_images = self.model_image_widget.get_images()
        work_images = self.work_image_widget.get_images()
        program_images = self.program_image_widget.get_images()
        vehicle_images = self.vehicle_image_widget.get_images()

        image_type_names = {
            "model": ("模型展示", "include_model_display"),
            "work": ("精彩瞬间", "include_work_display"),
            "program": ("程序展示", "include_program_display"),
            "vehicle": ("车辆展示", "include_vehicle_display"),
        }

        image_lists = {
            "model": model_images,
            "work": work_images,
            "program": program_images,
            "vehicle": vehicle_images,
        }

        for key, (display_name, config_key) in image_type_names.items():
            if layout_config.get(config_key, False):
                img_list = image_lists.get(key, [])
                if not img_list or len(img_list) == 0:
                    issues.append(f"{display_name}页已勾选但未上传图片")

        # 检查5: 补充说明未修改（基于会话初始值）
        current_comments = data.additional_comments.strip()
        if current_comments:  # 只有非空时才比较
            student_name = data.student_name
            if student_name and student_name in self._session_initial_comments:
                initial_comments = self._session_initial_comments[student_name]
                if current_comments == initial_comments:
                    issues.append("补充说明与本次会话初始值相同（未修改）")

        return len(issues) == 0, issues

    def _show_content_check_dialog(self, issues: list[str]) -> bool:
        """
        显示内容检查提示对话框

        Args:
            issues: 问题列表

        Returns:
            True: 继续生成 | False: 返回修改
        """
        message = "以下内容建议检查：\n\n" + "\n".join(f"- {issue}" for issue in issues)
        message += "\n\n是否仍要继续生成PPT？"

        reply = QMessageBox.question(
            self, "内容检查提示", message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # 默认选中"否"
        )

        return reply == QMessageBox.Yes

    def _on_generate_ppt(self):
        """生成PPT"""
        # 收集数据
        self._collect_data()

        if not self.current_data.student_name:
            QMessageBox.warning(self, "警告", "请输入学生姓名")
            return

        if not self.current_data.course_content:
            QMessageBox.warning(self, "警告", "请输入课程内容")
            return

        # 内容检查
        should_continue, issues = self._check_content_before_generation()
        if not should_continue:
            if not self._show_content_check_dialog(issues):
                return

        # 选择保存路径（使用班级特定路径）
        class_id = self.class_selector.get_current_class_id()
        output_dir = self.config_manager.get_class_output_path(class_id) if class_id else self.config_manager.get_output_path()
        default_path = str(Path(output_dir) / f"{self.current_data.student_name}_课程反馈.pptx")
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存PPT",
            default_path,
            "PowerPoint文件 (*.pptx);;所有文件 (*)"
        )

        # 保存用户选择的路径
        if file_path and class_id:
            self.config_manager.set_class_output_path(class_id, str(Path(file_path).parent))

        if file_path:
            try:
                self.update_status("正在生成PPT...")

                # 收集图片数据并计算数量
                model_images = self.model_image_widget.get_images()
                work_images = self.work_image_widget.get_images()
                program_images = self.program_image_widget.get_images()
                vehicle_images = self.vehicle_image_widget.get_images()

                # 根据勾选状态和图片数量决定各类型页数
                # 使用 layout_selector 的当前配置（班级级别配置），而非全局配置
                config_dict = self.layout_selector.get_config()
                self.current_layout_config = LayoutConfig(**config_dict)

                # 计算各类型页面数量
                model_image_count = len(model_images) if model_images and self.current_layout_config.include_model_display else 0
                work_image_count = len(work_images) if work_images and self.current_layout_config.include_work_display else 0
                program_image_count = len(program_images) if program_images and self.current_layout_config.include_program_display else 0
                vehicle_image_count = len(vehicle_images) if vehicle_images and self.current_layout_config.include_vehicle_display else 0

                # 重新加载模板
                self.ppt_generator._load_template()

                # 判断是否为第1课（第1课包含封面，其他课不包含）
                include_cover = (self.current_data.lesson_number == 1)

                # 根据配置生成（传递图片数量）
                self.ppt_generator.generate_from_template(
                    self.current_layout_config,
                    model_image_count=model_image_count,
                    work_image_count=work_image_count,
                    program_image_count=program_image_count,
                    vehicle_image_count=vehicle_image_count,
                    include_cover=include_cover
                )

                # 获取当前选择的课程系列
                series_name, series_level = self.series_selector.get_current_series()

                # 填充课程信息页内容（传递图片数量用于计算各页面起始位置）
                from src.core.content_filler import fill_ppt_content, verify_series_replacement
                fill_ppt_content(
                    self.ppt_generator.prs, self.current_data, series_name, series_level,
                    model_image_count=model_image_count,
                    work_image_count=work_image_count,
                    program_image_count=program_image_count,
                    vehicle_image_count=vehicle_image_count,
                    include_cover=include_cover
                )

                # 验证系列名称替换
                verify_ok, verify_errors = verify_series_replacement(
                    self.ppt_generator.prs, series_name, series_level, include_cover
                )
                if not verify_ok:
                    error_msg = "系列名称替换验证失败:\n" + "\n".join(verify_errors)
                    print(f"警告: {error_msg}")
                    # 继续执行但记录警告

                # 保存
                success, path = self.ppt_generator.save_course_unit(
                    str(Path(file_path).parent),
                    self.current_data
                )

                # 事件追踪：PPT 导出
                if success:
                    export_tracker = getattr(self, '_event_tracker', None)
                    if export_tracker:
                        file_size = Path(path).stat().st_size if Path(path).exists() else 0
                        export_tracker.track_export(format="pptx", file_size=file_size)

                if success:
                    # 事件追踪：PPT 生成完成
                    tracker = getattr(self, '_event_tracker', None)
                    if tracker:
                        import time
                        duration = int(time.time() - getattr(self, '_generate_start_time', time.time()))
                        tracker.track_generate(
                            student_count=1,
                            template="basic",
                            duration_seconds=duration,
                        )

                    # 计算课程信息页索引（1-based）
                    # include_cover=True: 课程信息页是第2页
                    # include_cover=False: 课程信息页是第1页
                    course_info_slide_index = 2 if include_cover else 1

                    # 后处理：一次性完成高度调整和纵向分布（只打开 PPT 一次）
                    from src.core.content_filler import post_process_ppt
                    self.update_status("正在后处理 PPT...")
                    post_process_ppt(path, course_info_slide_index, keep_open=True)

                    # 构建结果消息
                    page_info = []
                    if model_image_count > 0:
                        page_info.append(f"模型展示页: {model_image_count}页")
                    if work_image_count > 0:
                        page_info.append(f"精彩瞬间: {work_image_count}页")
                    if program_image_count > 0:
                        page_info.append(f"程序展示页: {program_image_count}页")
                    if vehicle_image_count > 0:
                        page_info.append(f"车辆展示页: {vehicle_image_count}页")

                    if verify_ok:
                        msg = f"PPT已生成:\n{path}\n\n系列名称验证通过\n" + "\n".join(page_info)
                    else:
                        msg = f"PPT已生成:\n{path}\n\n警告: 系列名称可能未正确替换\n" + "\n".join(verify_errors[:3])

                    self.update_status(f"PPT已生成: {Path(file_path).name}")
                    QMessageBox.information(self, "成功", msg)

                    # 成功生成后，记录该学员本次会话已生成（关闭时统一+1）
                    student_name = self.current_data.student_name
                    if student_name:
                        self._session_generated_students.add(student_name)

                    # 记录最近使用的数据
                    self.config_manager.add_recent_student(self.current_data.student_name)
                    if self.current_data.teacher_name:
                        self.config_manager.add_recent_teacher(self.current_data.teacher_name)
                else:
                    QMessageBox.warning(self, "错误", "PPT生成失败")

            except Exception as e:
                import traceback
                traceback.print_exc()
                QMessageBox.warning(self, "错误", f"生成失败: {e}")

    def _on_batch_generate_ppt(self):
        """批量生成PPT"""
        # 1. 保存当前学员数据
        self._save_current_student_data()

        # 2. 更新共享数据
        self._update_shared_data_from_forms()

        # 3. 内容检查
        should_continue, issues = self._check_content_before_generation(is_batch=True)
        if not should_continue:
            if not self._show_content_check_dialog(issues):
                return

        # 4. 获取选中生成的学员列表
        selected = self.student_tab_bar.get_selected_for_generation()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要生成的学员（点击学员后的 ✓ 按钮）")
            return

        # 5. 确认生成
        reply = QMessageBox.question(
            self, "确认批量生成",
            f"将为 {len(selected)} 位学员生成PPT：\n{', '.join(selected)}\n\n是否继续？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # 6. 选择输出目录（使用班级特定路径）
        class_id = self.class_selector.get_current_class_id()
        default_dir = self.config_manager.get_class_output_path(class_id) if class_id else self.config_manager.get_output_path()
        output_dir = QFileDialog.getExistingDirectory(
            self, "选择输出目录",
            default_dir
        )
        # 保存用户选择的路径
        if output_dir and class_id:
            self.config_manager.set_class_output_path(class_id, output_dir)
        if not output_dir:
            return

        # 7. 获取模板路径（转换为绝对路径）
        template_path = self.config_manager.get_template_path()
        if not Path(template_path).is_absolute():
            template_path = str(get_base_path() / template_path)

        # 8. 获取当前布局配置（过滤无效字段）
        config_dict = self.layout_selector.get_config()
        valid_fields = {
            'include_course_info', 'include_model_display', 'model_display_count',
            'include_double_image', 'include_program_display', 'include_vehicle_display',
            'include_work_display'
        }
        filtered_config = {k: v for k, v in config_dict.items() if k in valid_fields}
        layout_config = LayoutConfig(**filtered_config)

        # 9. 获取当前课程系列
        series_name, series_level = self.series_selector.get_current_series()

        # 10. 获取课程基本信息（共享）
        info = self.course_info_widget.get_data()
        lesson_number = info["lesson_number"]
        course_content = info["course_content"]
        teacher_name = info["teacher_name"]
        class_hours = info["class_hours"]
        class_date = info["class_date"]

        # 11. 收集每个学员的数据
        data_list = []
        for name in selected:
            data = self._prepare_student_data_for_generation(
                name,
                lesson_number,
                course_content,
                teacher_name,
                class_hours,
                class_date,
                series_name,
                series_level
            )
            data_list.append(data)

        # 12. 打开进度对话框开始生成
        dialog = BatchProgressDialog(self)
        dialog.start_generation(
            data_list, output_dir, template_path, layout_config,
            series_name=series_name,
            series_level=series_level
        )
        dialog.exec_()

        # 13. 检查生成结果，成功生成的学员记录到会话集合（关闭时统一+1）
        result = dialog.get_result()
        if result and result.success > 0:
            # 记录这些学员本次会话已生成
            for task in result.tasks:
                if task.status == "success":
                    self._session_generated_students.add(task.data.student_name)

    def _prepare_student_data_for_generation(
        self,
        student_name: str,
        lesson_number: int,
        course_content: str,
        teacher_name: str,
        class_hours: int,
        class_date,
        series_name: str,
        series_level: int
    ) -> CourseUnitData:
        """
        为指定学员准备生成数据

        合并共享数据（知识内容、作业、注意事项、图片）
        使用学员的独立数据（评价、补充说明、课时编号）

        Args:
            student_name: 学员姓名
            lesson_number: 课次（已废弃，现从配置获取学员独立课时）
            course_content: 课程内容
            teacher_name: 教师姓名
            class_hours: 课时
            class_date: 上课日期
            series_name: 系列名称
            series_level: 系列等级

        Returns:
            完整的 CourseUnitData
        """
        from src.core.models import EvaluationLevel

        # 创建新数据对象
        data = CourseUnitData()

        # 设置基本信息
        data.student_name = student_name
        # 获取学员独立的课时编号（优先从缓存获取，保持会话期间一致）
        if student_name in self._student_data_cache:
            data.lesson_number = self._student_data_cache[student_name].lesson_number
        else:
            current_class_id = self._current_class_id
            if current_class_id:
                data.lesson_number = self.config_manager.get_student_next_lesson_number(current_class_id, student_name)
            else:
                data.lesson_number = lesson_number  # 后备使用传入值
        data.course_content = course_content
        data.teacher_name = teacher_name
        data.class_hours = class_hours
        data.class_date = class_date

        # 合并共享数据
        if self._class_shared_data:
            data.knowledge_content = self._class_shared_data.knowledge_content
            data.knowledge_html = self._class_shared_data.knowledge_html
            data.highlights = self._class_shared_data.highlights
            data.difficulties = self._class_shared_data.difficulties
            data.homework = self._class_shared_data.homework
            data.other_notes = self._class_shared_data.other_notes
            # 图片：只合并启用了同步的字段
            if self._image_sync_states['model_images']:
                data.model_images = self._class_shared_data.model_images
            if self._image_sync_states['program_images']:
                data.program_images = self._class_shared_data.program_images
            if self._image_sync_states['vehicle_images']:
                data.vehicle_images = self._class_shared_data.vehicle_images

        # 使用学员的独立数据（评价、补充说明）
        if student_name in self._student_data_cache:
            print(f"[DEBUG] _prepare_student_data_for_generation: {student_name} 在缓存中，使用缓存数据")
            cached = self._student_data_cache[student_name]
            # 调试：打印缓存中的关键评价值
            print(f"[DEBUG] 缓存中的评价: logic_thinking={getattr(cached, 'logic_thinking', 'N/A')}, "
                  f"overall_evaluation={getattr(cached, 'overall_evaluation', 'N/A')}, "
                  f"last_homework_status={getattr(cached, 'last_homework_status', 'N/A')}")
            # 复制12项评价
            for key in ["logic_thinking", "content_understanding", "task_completion",
                        "listening_habit", "problem_solving", "independent_analysis",
                        "knowledge_proficiency", "imagination_creativity", "frustration_handling",
                        "learning_method", "hands_on_ability", "focus_efficiency"]:
                setattr(data, key, getattr(cached, key, EvaluationLevel.NOT_SHOWN))
            # 复制总体评价
            data.overall_evaluation = cached.overall_evaluation
            # 复制上次作业
            data.last_homework_status = cached.last_homework_status
            # 复制补充说明
            data.additional_comments = cached.additional_comments
            # 精彩瞬间图片（始终独立）
            data.work_images = cached.work_images
            # 非同步状态的图片从学员缓存获取
            if not self._image_sync_states['model_images']:
                data.model_images = cached.model_images
            if not self._image_sync_states['program_images']:
                data.program_images = cached.program_images
            if not self._image_sync_states['vehicle_images']:
                data.vehicle_images = cached.vehicle_images
        else:
            # 学员没有缓存数据，从持久化加载评价（而不是使用默认值）
            print(f"[DEBUG] _prepare_student_data_for_generation: {student_name} 不在缓存中，从持久化加载")
            current_class_id = self.class_selector.get_current_class_id()
            print(f"[DEBUG] current_class_id = {current_class_id}")
            if current_class_id:
                last_eval = self.config_manager.get_student_last_evaluation(current_class_id, student_name)
                print(f"[DEBUG] last_eval = {last_eval}")
                # 评价相关字段列表（任一字段存在即认为有历史评价）
                evaluation_keys = [
                    "logic_thinking", "content_understanding", "task_completion",
                    "listening_habit", "problem_solving", "independent_analysis",
                    "knowledge_proficiency", "imagination_creativity", "frustration_handling",
                    "learning_method", "hands_on_ability", "focus_efficiency",
                    "overall_evaluation", "last_homework_status"
                ]
                if last_eval and any(key in last_eval for key in evaluation_keys):
                    print("[DEBUG] 找到历史评价，调用 _apply_last_evaluation_to_data")
                    self._apply_last_evaluation_to_data(data, last_eval)
                else:
                    # 没有历史评价数据，使用默认值
                    print("[DEBUG] 没有历史评价，使用默认值")
                    self._set_default_evaluation(data)
            else:
                # 没有班级信息，使用默认值
                print("[DEBUG] 没有班级信息，使用默认值")
                self._set_default_evaluation(data)
            data.additional_comments = ""

        return data

    def _on_clear_form(self):
        """清空表单"""
        reply = QMessageBox.question(
            self, "确认清空", "确定要清空所有输入内容吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.course_info_widget.clear()
            self.knowledge_editor.clear()
            self.evaluation_widget.clear()
            self.model_image_widget.clear_images()
            self.work_image_widget.clear_images()
            self.program_image_widget.clear_images()
            self.vehicle_image_widget.clear_images()
            self.update_status("表单已清空")

    def _on_reset_defaults(self):
        """重置为默认设置"""
        reply = QMessageBox.question(
            self, "确认重置", "确定要重置所有设置为默认值吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.config_manager.reset_to_defaults()
            self.layout_selector.set_config(self.config_manager.get_layout_config())
            self.update_status("已重置为默认设置")

    def _on_toggle_toolbar(self, checked):
        """显示/隐藏工具栏"""
        self.toolbar.setVisible(checked)

    def _on_toggle_statusbar(self, checked):
        """显示/隐藏状态栏"""
        self.statusBar().setVisible(checked)

    def _on_toggle_theme(self, checked):
        """切换主题"""
        theme = "dark" if checked else "light"
        ThemeManager.instance().set_theme(theme)
        self.config_manager.set_theme(theme)

    def _on_theme_changed(self, theme_name: str):
        """主题改变时的回调"""
        try:
            colors = ThemeManager.instance().get_colors()

            # 使用主窗口样式表
            self.setStyleSheet(f"""
                QMainWindow {{
                    background-color: {colors.background_primary};
                }}
                QWidget {{
                    background-color: {colors.background_primary};
                    color: {colors.text_primary};
                }}
                QTabWidget::pane {{
                    border: 1px solid {colors.border_normal};
                    background-color: {colors.background_primary};
                }}
                QTabBar::tab {{
                    background-color: {colors.button_normal};
                    color: {colors.text_primary};
                    border: 1px solid {colors.border_normal};
                    padding: 4px 12px;
                }}
                QTabBar::tab:selected {{
                    background-color: {colors.primary};
                    color: white;
                }}
                QMenuBar {{
                    background-color: {colors.background_secondary};
                    color: {colors.text_primary};
                }}
                QMenuBar::item:selected {{
                    background-color: {colors.primary};
                    color: white;
                }}
                QMenu {{
                    background-color: {colors.background_secondary};
                    color: {colors.text_primary};
                }}
                QMenu::item:selected {{
                    background-color: {colors.primary};
                    color: white;
                }}
                QToolBar {{
                    background-color: {colors.background_secondary};
                    border: none;
                    spacing: 3px;
                    padding: 3px;
                }}
                QStatusBar {{
                    background-color: {colors.background_secondary};
                    color: {colors.text_secondary};
                }}
                QLabel {{
                    color: {colors.text_primary};
                    background: transparent;
                }}
                QLineEdit, QTextEdit, QPlainTextEdit {{
                    background-color: {colors.background_primary};
                    color: {colors.text_primary};
                    border: 1px solid {colors.border_normal};
                }}
                QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                    border-color: {colors.border_focused};
                }}
                QComboBox {{
                    background-color: {colors.background_primary};
                    color: {colors.text_primary};
                    border: 1px solid {colors.border_normal};
                }}
                QComboBox:drop-down {{
                    border: none;
                }}
                QComboBox QAbstractItemView {{
                    background-color: {colors.background_primary};
                    color: {colors.text_primary};
                    selection-background-color: {colors.primary};
                }}
                QSpinBox {{
                    background-color: {colors.background_primary};
                    color: {colors.text_primary};
                    border: 1px solid {colors.border_normal};
                    padding: 2px;
                    padding-right: 20px;
                }}
                QSpinBox::up-button {{
                    subcontrol-origin: border;
                    subcontrol-position: top right;
                    width: 18px;
                    border-left: 1px solid {colors.border_normal};
                    background-color: {colors.background_tertiary};
                }}
                QSpinBox::down-button {{
                    subcontrol-origin: border;
                    subcontrol-position: bottom right;
                    width: 18px;
                    border-top: 1px solid {colors.border_normal};
                    border-left: 1px solid {colors.border_normal};
                    background-color: {colors.background_tertiary};
                }}
                QSpinBox::up-button:hover {{
                    background-color: {colors.border_normal};
                }}
                QSpinBox::down-button:hover {{
                    background-color: {colors.border_normal};
                }}
                QCheckBox {{
                    color: {colors.text_primary};
                }}
                QCheckBox::indicator {{
                    width: 16px;
                    height: 16px;
                    border: 1px solid {colors.border_normal};
                    background-color: {colors.background_primary};
                    border-radius: 3px;
                }}
                QCheckBox::indicator:checked {{
                    background-color: {colors.primary};
                    border-color: {colors.primary};
                }}
                QPushButton {{
                    background-color: {colors.button_normal};
                    color: {colors.text_primary};
                    border: 1px solid {colors.border_normal};
                    border-radius: 4px;
                    padding: 4px 12px;
                }}
                QPushButton:hover {{
                    background-color: {colors.background_tertiary};
                }}
                QPushButton:pressed {{
                    background-color: {colors.primary};
                    color: white;
                }}
                QListWidget {{
                    background-color: {colors.background_primary};
                    color: {colors.text_primary};
                    border: 1px solid {colors.border_normal};
                }}
                QListWidget::item {{
                    padding: 2px;
                }}
                QListWidget::item:selected {{
                    background-color: {colors.primary};
                    color: white;
                }}
                QListWidget::item:hover {{
                    background-color: {colors.background_tertiary};
                }}
                QScrollArea {{
                    background-color: {colors.scroll_area_background};
                    border: none;
                }}
                QScrollBar:vertical {{
                    background-color: {colors.background_secondary};
                    width: 10px;
                }}
                QScrollBar::handle:vertical {{
                    background-color: {colors.border_normal};
                    border-radius: 5px;
                    min-height: 20px;
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                    height: 0px;
                }}
                QScrollBar:horizontal {{
                    background-color: {colors.background_secondary};
                    height: 10px;
                }}
                QScrollBar::handle:horizontal {{
                    background-color: {colors.border_normal};
                    border-radius: 5px;
                    min-width: 20px;
                }}
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                    width: 0px;
                }}
                QSplitter::handle {{
                    background-color: {colors.border_normal};
                }}
                QGroupBox {{
                    color: {colors.text_primary};
                    border: 1px solid {colors.border_normal};
                    border-radius: 4px;
                    margin-top: 10px;
                    padding-top: 10px;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }}
                QRadioButton {{
                    color: {colors.text_primary};
                }}
                QRadioButton::indicator {{
                    width: 16px;
                    height: 16px;
                    border: 1px solid {colors.border_normal};
                    background-color: {colors.background_primary};
                    border-radius: 8px;
                }}
                QRadioButton::indicator:checked {{
                    background-color: {colors.primary};
                    border-color: {colors.primary};
                }}
            """)

            # 强制重绘
            self.repaint()
        except Exception as e:
            print(f"[ERROR] 主题切换失败: {e}")
            import traceback
            traceback.print_exc()

    def _on_about(self):
        """关于对话框"""
        QMessageBox.about(
            self, "关于",
            "<h3>法贝实验室课程反馈助手</h3>"
            "<p>版本: 1.0.0</p>"
            "<p>自动生成课程反馈PPT的桌面应用程序</p>"
        )

    def update_status(self, message: str):
        """更新状态栏"""
        self.status_label.setText(message)


def _send_heartbeat(client, window):
    """发送心跳保活 — 403 时强制退出"""
    import asyncio
    try:
        result = asyncio.run(client.auth.check_auth())
        if not result:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(window, "会话过期", "登录已过期，请重新登录")
            QApplication.quit()
    except Exception:
        pass  # 网络异常不强制退出


def run_app(client=None):
    """运行应用程序"""
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("法贝实验室课程反馈助手")
    app.setApplicationVersion("1.0.0")
    app.setStyle('Fusion')

    window = MainWindow()
    # 挂载事件追踪器 + 心跳定时器
    if client is not None:
        import platform
        from src.core.event_tracker import EventTracker
        tracker = EventTracker(client=client)
        window._event_tracker = tracker

        # 事件追踪：应用启动
        tracker.track_app_start(version="1.0.0", os_info=platform.platform())

        # 心跳：每 5 分钟发送一次
        from PyQt5.QtCore import QTimer
        heartbeat_timer = QTimer(window)
        heartbeat_timer.timeout.connect(lambda: _send_heartbeat(client, window))
        heartbeat_timer.start(5 * 60 * 1000)  # 5 分钟
        window._heartbeat_timer = heartbeat_timer
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    run_app()
