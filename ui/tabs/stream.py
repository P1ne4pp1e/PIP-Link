from ui.components.label import Label
from ui.components.textbox import TextBox
from ui.components.button import Button


class StreamTab:
    """流参数选项卡"""

    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.components = []

        # 立即创建输入框和按钮（在__init__中）
        self.jpeg_quality_textbox = TextBox(10, 225, 240, 36, "jpeg_quality")
        self.jpeg_quality_textbox.placeholder = "80"
        self.jpeg_quality_textbox.max_length = 3
        self.jpeg_quality_textbox.font_scale = 0.5

        self.frame_scale_textbox = TextBox(260, 225, 240, 36, "frame_scale")
        self.frame_scale_textbox.placeholder = "1.0"
        self.frame_scale_textbox.max_length = 4
        self.frame_scale_textbox.font_scale = 0.5

        self.apply_button = Button(10, 275, 490, 40, "Apply Quality Settings", "apply_quality")
        self.apply_button.background_color = (70, 130, 180)
        self.apply_button.font_scale = 0.55

        self._build_labels()

    def _build_labels(self):
        """创建标签"""
        self.resolution_label = Label(10, 10, 510, 25, "", "resolution")
        self.resolution_label.text_color = (240, 240, 245)
        self.resolution_label.background_color = (45, 45, 52)
        self.resolution_label.font_scale = 0.5
        self.resolution_label.font_thickness = 2

        self.quality_label = Label(10, 40, 510, 25, "", "quality")
        self.quality_label.text_color = (240, 240, 245)
        self.quality_label.background_color = (45, 45, 52)
        self.quality_label.font_scale = 0.5
        self.quality_label.font_thickness = 2

        self.scale_label = Label(10, 70, 510, 25, "", "scale")
        self.scale_label.text_color = (240, 240, 245)
        self.scale_label.background_color = (45, 45, 52)
        self.scale_label.font_scale = 0.5
        self.scale_label.font_thickness = 2

        self.fps_label = Label(10, 100, 510, 25, "", "fps")
        self.fps_label.text_color = (240, 240, 245)
        self.fps_label.background_color = (45, 45, 52)
        self.fps_label.font_scale = 0.5
        self.fps_label.font_thickness = 2

        self.actual_fps_label = Label(10, 130, 510, 25, "", "actual_fps")
        self.actual_fps_label.text_color = (240, 240, 245)
        self.actual_fps_label.background_color = (45, 45, 52)
        self.actual_fps_label.font_scale = 0.5
        self.actual_fps_label.font_thickness = 2

    def update(self, stream_params):
        """更新显示"""
        self.components = []

        if not stream_params:
            no_data = Label(10, 10, 510, 25, "No stream parameters received", "no_data")
            no_data.text_color = (150, 150, 150)
            no_data.background_color = (45, 45, 52)
            no_data.font_scale = 0.5
            self.components.append(no_data)
            return

        # 更新标签文本
        self.resolution_label.text = f"Resolution: {stream_params.resolution_w}x{stream_params.resolution_h}"
        self.quality_label.text = f"JPEG Quality: {stream_params.jpeg_quality}%"
        self.scale_label.text = f"Frame Scale: {stream_params.frame_scale:.0%}"
        self.fps_label.text = f"Target FPS: {stream_params.target_fps}"
        self.actual_fps_label.text = f"Actual FPS: {stream_params.actual_fps:.1f}"

        # 添加到组件列表
        self.components.extend([
            self.resolution_label,
            self.quality_label,
            self.scale_label,
            self.fps_label,
            self.actual_fps_label
        ])

        # 质量控制标签
        control_label = Label(10, 170, 510, 20, "Quality Control:", "control_label")
        control_label.text_color = (100, 200, 255)
        control_label.background_color = (45, 45, 52)
        control_label.font_scale = 0.5
        control_label.font_thickness = 2
        self.components.append(control_label)

        jpeg_label = Label(10, 200, 510, 20, "JPEG Quality (1-100):", "jpeg_label")
        jpeg_label.text_color = (200, 200, 200)
        jpeg_label.background_color = (45, 45, 52)
        jpeg_label.font_scale = 0.45
        self.components.append(jpeg_label)

        # 更新TextBox默认值
        if not self.jpeg_quality_textbox.is_focused and not self.jpeg_quality_textbox.text:
            self.jpeg_quality_textbox.text = str(stream_params.jpeg_quality)

        self.components.append(self.jpeg_quality_textbox)

        scale_input_label = Label(260, 200, 250, 20, "Frame Scale (0.1-1.0):", "scale_input_label")
        scale_input_label.text_color = (200, 200, 200)
        scale_input_label.background_color = (45, 45, 52)
        scale_input_label.font_scale = 0.45
        self.components.append(scale_input_label)

        if not self.frame_scale_textbox.is_focused and not self.frame_scale_textbox.text:
            self.frame_scale_textbox.text = f"{stream_params.frame_scale:.2f}"

        self.components.append(self.frame_scale_textbox)
        self.components.append(self.apply_button)

    def get_components(self):
        return self.components

    def get_input_values(self):
        """获取输入值"""
        try:
            jpeg_quality = int(self.jpeg_quality_textbox.text) if self.jpeg_quality_textbox.text else 80
            frame_scale = float(self.frame_scale_textbox.text) if self.frame_scale_textbox.text else 1.0
            return {
                'jpeg_quality': max(1, min(100, jpeg_quality)),
                'frame_scale': max(0.1, min(1.0, frame_scale))
            }
        except ValueError:
            return None