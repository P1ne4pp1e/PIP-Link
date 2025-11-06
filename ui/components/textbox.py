import cv2
import numpy as np
from typing import Optional, Callable
from ui.components.base_object import Object

class TextBox(Object):
    """文本输入框组件"""

    def __init__(self, x: int, y: int, width: int, height: int, name: str = ""):
        super().__init__(x, y, width, height, name or "textbox")
        self.text = ""
        self.placeholder = "Input text..."
        self.text_color = (0, 0, 0)
        self.placeholder_color = (150, 150, 150)
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.5
        self.font_thickness = 1

        # 输入框样式
        self.background_color = (255, 255, 255)
        self.border_color = (180, 180, 180)
        self.focus_border_color = (70, 130, 180)
        self.border_width = 2

        # 焦点状态
        self.is_focused = False
        self.cursor_visible = True
        self.cursor_blink_time = 0
        self.cursor_blink_interval = 0.5  # 秒

        # 文本编辑
        self.max_length = 50
        self.on_text_change: Optional[Callable] = None

    def handle_mouse_event(self, event: int, x: int, y: int, flags: int, param):
        if not self.visible or not self.enabled:
            return False

        is_inside = self.contains_point(x, y)

        # 处理点击获取焦点
        if event == cv2.EVENT_LBUTTONDOWN:
            if is_inside:
                self.is_focused = True
                Object.set_focus(self)  # 设置全局焦点
                return True
            else:
                self.is_focused = False
                Object.set_focus(None)  # 移除焦点

        return super().handle_mouse_event(event, x, y, flags, param)

    def on_blur(self):
        """失去焦点时的回调"""
        self.is_focused = False
        self.cursor_visible = True
        self.cursor_blink_time = 0

    def handle_key(self, key: int) -> bool:
        """处理键盘输入"""
        if not self.is_focused or not self.enabled:
            return False

        # Backspace
        if key == 8:
            if self.text:
                self.text = self.text[:-1]
                if self.on_text_change:
                    self.on_text_change(self)
            return True

        # Enter
        elif key == 13:
            self.is_focused = False
            Object.set_focus(None)  # 清除焦点
            return True

        # ESC
        elif key == 27:
            self.is_focused = False
            Object.set_focus(None)  # 清除焦点
            return True

        # 普通字符
        elif 32 <= key <= 126:
            if len(self.text) < self.max_length:
                char = chr(key)
                # 只允许数字、小数点、减号
                if char.isdigit() or char in '.-':
                    self.text += char
                    if self.on_text_change:
                        self.on_text_change(self)
            return True

        return False

    def update(self, dt: float = 0):
        """更新光标闪烁"""
        super().update(dt)
        if self.is_focused and dt > 0:
            self.cursor_blink_time += dt
            if self.cursor_blink_time >= self.cursor_blink_interval:
                self.cursor_visible = not self.cursor_visible
                self.cursor_blink_time = 0

    def draw(self, canvas: np.ndarray):
        if not self.visible:
            return

        ax, ay = self.absolute_position

        # 绘制背景
        cv2.rectangle(canvas, (ax, ay),
                      (ax + self.width, ay + self.height),
                      self.background_color, -1)

        # 绘制边框（焦点时高亮）
        border_color = self.focus_border_color if self.is_focused else self.border_color
        cv2.rectangle(canvas, (ax, ay),
                      (ax + self.width, ay + self.height),
                      border_color, self.border_width)

        # 绘制文本或占位符
        display_text = self.text if self.text else self.placeholder
        text_color = self.text_color if self.text else self.placeholder_color

        text_size = cv2.getTextSize(display_text, self.font, self.font_scale, self.font_thickness)[0]
        text_x = ax + 10
        text_y = ay + (self.height + text_size[1]) // 2

        # 裁剪文本以适应宽度
        max_text_width = self.width - 30
        if text_size[0] > max_text_width:
            # 从右边开始显示
            for i in range(len(display_text)):
                sub_text = display_text[i:]
                sub_size = cv2.getTextSize(sub_text, self.font, self.font_scale, self.font_thickness)[0]
                if sub_size[0] <= max_text_width:
                    display_text = sub_text
                    break

        cv2.putText(canvas, display_text, (text_x, text_y),
                    self.font, self.font_scale, text_color, self.font_thickness)

        # 绘制光标
        if self.is_focused and self.cursor_visible and self.text:
            cursor_x = text_x + cv2.getTextSize(display_text, self.font,
                                                self.font_scale, self.font_thickness)[0][0] + 2
            cv2.line(canvas, (cursor_x, ay + 8), (cursor_x, ay + self.height - 8),
                     self.text_color, 2)

        # 绘制子对象
        for child in self.children:
            child.draw(canvas)
