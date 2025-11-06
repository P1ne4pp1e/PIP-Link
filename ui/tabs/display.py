from ui.components.label import Label
from ui.components.button import Button
from core.config import Config


class DisplayTab:
    """显示设置选项卡"""

    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.components = []
        self.resolution_buttons = []

        # 立即创建按钮（不等待update调用）
        self.windowed_btn = Button(10, 35, 250, 40, "Windowed Mode", "windowed_btn")
        self.windowed_btn.font_scale = 0.55

        self.fullscreen_btn = Button(270, 35, 250, 40, "Fullscreen Mode", "fullscreen_btn")
        self.fullscreen_btn.font_scale = 0.55

        # 预创建分辨率按钮
        self._create_resolution_buttons()

    def _create_resolution_buttons(self):
        """预创建分辨率按钮"""
        y_offset = 155
        self.resolution_buttons = []

        for idx, (name, res) in enumerate(Config.AVAILABLE_RESOLUTIONS):
            col = idx % 2
            row = idx // 2
            x = 10 + col * 260
            y = y_offset + row * 45

            btn = Button(x, y, 250, 38, name.split()[0], f"res_btn_{idx}")
            btn.font_scale = 0.5
            self.resolution_buttons.append(btn)

    def update(self, window_mode, current_resolution_index):
        """更新显示"""
        self.components = []

        # 窗口模式标签
        mode_label = Label(10, 10, 510, 20, "Window Mode:", "mode_label")
        mode_label.text_color = (200, 200, 200)
        mode_label.background_color = (45, 45, 52)
        mode_label.font_scale = 0.45
        mode_label.align = "left"
        self.components.append(mode_label)

        # 更新窗口模式按钮状态
        self.windowed_btn.background_color = (70, 130, 180) if window_mode == "windowed" else (55, 55, 62)
        self.fullscreen_btn.background_color = (70, 130, 180) if window_mode == "fullscreen" else (55, 55, 62)

        self.components.append(self.windowed_btn)
        self.components.append(self.fullscreen_btn)

        # 分辨率标签
        res_label = Label(10, 90, 510, 20, "Resolution (Windowed Mode Only):", "res_label")
        res_label.text_color = (200, 200, 200)
        res_label.background_color = (45, 45, 52)
        res_label.font_scale = 0.45
        res_label.align = "left"
        self.components.append(res_label)

        # 当前分辨率显示
        current_res_name, current_res = Config.AVAILABLE_RESOLUTIONS[current_resolution_index]
        current_label = Label(10, 115, 510, 30, f"Current: {current_res_name}", "current_res")
        current_label.text_color = (100, 200, 255)
        current_label.background_color = (45, 45, 52)
        current_label.font_scale = 0.5
        current_label.font_thickness = 2
        current_label.align = "center"
        self.components.append(current_label)

        # 更新分辨率按钮状态
        for idx, btn in enumerate(self.resolution_buttons):
            if window_mode == "windowed":
                if idx == current_resolution_index:
                    btn.background_color = (70, 130, 180)
                else:
                    btn.background_color = (60, 60, 67)
                    btn.hover_color = (80, 80, 87)
                btn.enabled = True
            else:
                btn.background_color = (40, 40, 45)
                btn.enabled = False

            self.components.append(btn)

    def get_components(self):
        """返回UI组件列表"""
        return self.components