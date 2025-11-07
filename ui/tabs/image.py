from ui.components.label import Label
from ui.components.textbox import TextBox
from ui.components.button import Button


class ImageTab:
    """图像调整选项卡"""

    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.components = []

        # 立即创建输入框和按钮
        self.exposure_textbox = TextBox(10, 140, 160, 36, "exposure_textbox")
        self.exposure_textbox.text = "1.00"
        self.exposure_textbox.placeholder = "1.0"
        self.exposure_textbox.max_length = 4
        self.exposure_textbox.font_scale = 0.5

        self.contrast_textbox = TextBox(180, 140, 160, 36, "contrast_textbox")
        self.contrast_textbox.text = "1.00"
        self.contrast_textbox.placeholder = "1.0"
        self.contrast_textbox.max_length = 4
        self.contrast_textbox.font_scale = 0.5

        self.gamma_textbox = TextBox(350, 140, 160, 36, "gamma_textbox")
        self.gamma_textbox.text = "1.00"
        self.gamma_textbox.placeholder = "1.0"
        self.gamma_textbox.max_length = 4
        self.gamma_textbox.font_scale = 0.5

        self.apply_button = Button(10, 190, 490, 40, "Apply Image Adjustment", "apply_image_btn")
        self.apply_button.background_color = (70, 130, 180)
        self.apply_button.hover_color = (90, 150, 200)
        self.apply_button.font_scale = 0.55

        self.reset_button = Button(10, 240, 240, 40, "Reset to Default", "reset_image_btn")
        self.reset_button.background_color = (180, 130, 70)
        self.reset_button.hover_color = (200, 150, 90)
        self.reset_button.font_scale = 0.5

        self.config_manager = None

        self._build_static_ui()

    def _build_static_ui(self):
        """构建静态UI元素"""
        self.title_label = Label(10, 10, 510, 25, "Image Adjustment", "image_title")
        self.title_label.text_color = (100, 200, 255)
        self.title_label.background_color = (45, 45, 52)
        self.title_label.font_scale = 0.5
        self.title_label.font_thickness = 2

        self.current_label = Label(10, 45, 510, 60, "", "current_values")
        self.current_label.text_color = (100, 255, 100)
        self.current_label.background_color = (45, 45, 52)
        self.current_label.font_scale = 0.45

        self.exposure_label = Label(10, 115, 160, 20, "Exposure (0.1-3.0):", "exposure_label")
        self.exposure_label.text_color = (200, 200, 200)
        self.exposure_label.background_color = (45, 45, 52)
        self.exposure_label.font_scale = 0.4

        self.contrast_label = Label(180, 115, 160, 20, "Contrast (0.1-3.0):", "contrast_label")
        self.contrast_label.text_color = (200, 200, 200)
        self.contrast_label.background_color = (45, 45, 52)
        self.contrast_label.font_scale = 0.4

        self.gamma_label = Label(350, 115, 160, 20, "Gamma (0.1-3.0):", "gamma_label")
        self.gamma_label.text_color = (200, 200, 200)
        self.gamma_label.background_color = (45, 45, 52)
        self.gamma_label.font_scale = 0.4

        self.info_label = Label(10, 295, 510, 80,
                                "Tip: Increase exposure for dark images.\nAdjust contrast to enhance details.\nModify gamma for brightness curve.\n\nValues shown above are from ROS2 server.",
                                "image_info")
        self.info_label.text_color = (150, 150, 155)
        self.info_label.background_color = (45, 45, 52)
        self.info_label.font_scale = 0.4

    def update(self, stream_params):
        """更新显示"""
        self.components = []

        # 添加静态UI
        self.components.extend([
            self.title_label,
            self.current_label,
            self.exposure_label,
            self.contrast_label,
            self.gamma_label,
            self.exposure_textbox,
            self.contrast_textbox,
            self.gamma_textbox,
            self.apply_button,
            self.reset_button,
            self.info_label
        ])

        if not stream_params:
            self.current_label.text = "No server data available\nConnect to server first"
            self.current_label.text_color = (150, 150, 150)
            return

        # 读取服务端参数
        server_exposure = getattr(stream_params, 'exposure', 1.0)
        server_contrast = getattr(stream_params, 'contrast', 1.0)
        server_gamma = getattr(stream_params, 'gamma', 1.0)

        self.current_label.text = f"Server Values:\nExposure: {server_exposure:.2f}  |  Contrast: {server_contrast:.2f}  |  Gamma: {server_gamma:.2f}"
        self.current_label.text_color = (100, 255, 100)

        # 只在未聚焦且为空时更新
        if not self.exposure_textbox.is_focused and not self.exposure_textbox.text:
            self.exposure_textbox.text = f"{server_exposure:.2f}"
        if not self.contrast_textbox.is_focused and not self.contrast_textbox.text:
            self.contrast_textbox.text = f"{server_contrast:.2f}"
        if not self.gamma_textbox.is_focused and not self.gamma_textbox.text:
            self.gamma_textbox.text = f"{server_gamma:.2f}"

    def set_config(self, config_manager):
        """设置配置管理器并加载配置"""
        self.config_manager = config_manager
        # 加载配置到输入框
        self.exposure_textbox.text = f"{config_manager.get('image', 'exposure', 1.0):.2f}"
        self.contrast_textbox.text = f"{config_manager.get('image', 'contrast', 1.0):.2f}"
        self.gamma_textbox.text = f"{config_manager.get('image', 'gamma', 1.0):.2f}"

    def get_components(self):
        return self.components

    def get_input_values(self):
        """获取输入值"""
        try:
            exposure = float(self.exposure_textbox.text) if self.exposure_textbox.text else 1.0
            contrast = float(self.contrast_textbox.text) if self.contrast_textbox.text else 1.0
            gamma = float(self.gamma_textbox.text) if self.gamma_textbox.text else 1.0

            return {
                'exposure': max(0.1, min(3.0, exposure)),
                'contrast': max(0.1, min(3.0, contrast)),
                'gamma': max(0.1, min(3.0, gamma))
            }
        except ValueError:
            return None