from ui.components.label import Label
from ui.components.textbox import TextBox
from ui.components.button import Button
from core.config import Config


class ControlTab:
    """控制设置选项卡"""

    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.components = []

        # 立即创建控件
        self.sensitivity_textbox = TextBox(10, 115, 490, 36, "sensitivity_textbox")
        self.sensitivity_textbox.text = f"{Config.DEFAULT_SENSITIVITY:.2f}"
        self.sensitivity_textbox.placeholder = "1.0"
        self.sensitivity_textbox.max_length = 4
        self.sensitivity_textbox.font_scale = 0.5

        self.apply_button = Button(10, 165, 490, 40, "Apply Sensitivity", "apply_sens_btn")
        self.apply_button.background_color = (70, 130, 180)
        self.apply_button.hover_color = (90, 150, 200)
        self.apply_button.font_scale = 0.55

        self._build_static_ui()

    def _build_static_ui(self):
        """构建静态UI元素"""
        self.title_label = Label(10, 10, 510, 25, "Mouse Control Settings", "control_title")
        self.title_label.text_color = (100, 200, 255)
        self.title_label.background_color = (45, 45, 52)
        self.title_label.font_scale = 0.5
        self.title_label.font_thickness = 2

        self.current_label = Label(10, 40, 510, 50, "", "current_sensitivity")
        self.current_label.text_color = (100, 255, 100)
        self.current_label.background_color = (45, 45, 52)
        self.current_label.font_scale = 0.45

        self.sens_label = Label(10, 90, 490, 20,
                                f"Sensitivity ({Config.MIN_SENSITIVITY:.1f}-{Config.MAX_SENSITIVITY:.1f}):",
                                "sens_label")
        self.sens_label.text_color = (200, 200, 200)
        self.sens_label.background_color = (45, 45, 52)
        self.sens_label.font_scale = 0.4

        self.info_label = Label(10, 220, 510, 100,
                                f"Current Settings:\n"
                                f"- Scale Factor: {Config.MOUSE_SCALE_FACTOR:.2f} (fixed)\n"
                                f"- Velocity Limit: {Config.MIN_MOUSE_VELOCITY:.0f} ~ {Config.MAX_MOUSE_VELOCITY:.0f} px/s\n\n"
                                f"Final velocity = raw_vel * sensitivity * scale_factor",
                                "control_info")
        self.info_label.text_color = (150, 150, 155)
        self.info_label.background_color = (45, 45, 52)
        self.info_label.font_scale = 0.4
        self.info_label.valign = "top"

    def update(self, current_sensitivity):
        """更新显示"""
        self.components = []

        # 添加静态UI
        self.components.extend([
            self.title_label,
            self.current_label,
            self.sens_label,
            self.sensitivity_textbox,
            self.apply_button,
            self.info_label
        ])

        # 更新当前灵敏度显示
        self.current_label.text = f"Current Sensitivity: {current_sensitivity:.2f}"

        # 只在未聚焦且为空时更新输入框
        if not self.sensitivity_textbox.is_focused and not self.sensitivity_textbox.text:
            self.sensitivity_textbox.text = f"{current_sensitivity:.2f}"

    def get_components(self):
        return self.components

    def get_input_values(self):
        """获取输入值"""
        try:
            sensitivity = float(self.sensitivity_textbox.text) if self.sensitivity_textbox.text else Config.DEFAULT_SENSITIVITY
            return {
                'sensitivity': max(Config.MIN_SENSITIVITY, min(Config.MAX_SENSITIVITY, sensitivity))
            }
        except ValueError:
            return None