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

        # 光标位置
        self.cursor_position = 0  # 光标在文本中的位置（0表示最前面）

        # 长按重复
        self.key_repeat_delay = 0.5  # 首次重复延迟（秒）
        self.key_repeat_interval = 0.03  # 重复间隔（秒）
        self.current_key = None  # 当前按下的键
        self.key_press_time = 0  # 按键按下时间
        self.last_repeat_time = 0  # 上次重复时间
        self.key_just_pressed = False  # 是否刚按下

        # 光标快速移动检测
        self.cursor_moving = False  # 光标是否在快速移动
        self.last_cursor_move_time = 0  # 上次移动时间
        self.cursor_move_timeout = 0.15  # 移动停止判定时间（秒）

        # 文本编辑
        self.max_length = 50
        self.on_text_change: Optional[Callable] = None

    def _process_key_action(self, key: int):
        """处理按键动作（用于首次按下和重复）"""
        import time

        # Backspace
        if key == 8:
            if self.text and self.cursor_position > 0:
                self.text = self.text[:self.cursor_position - 1] + self.text[self.cursor_position:]
                self.cursor_position -= 1
                if self.on_text_change:
                    self.on_text_change(self)

        # 左箭头
        elif key == 2:
            if self.cursor_position > 0:
                self.cursor_position -= 1
                # 标记光标正在移动
                self.cursor_moving = True
                self.last_cursor_move_time = time.time()

        # 右箭头
        elif key == 3:
            if self.cursor_position < len(self.text):
                self.cursor_position += 1
                # 标记光标正在移动
                self.cursor_moving = True
                self.last_cursor_move_time = time.time()

        # Delete键
        elif key == 127:
            if self.cursor_position < len(self.text):
                self.text = self.text[:self.cursor_position] + self.text[self.cursor_position + 1:]
                if self.on_text_change:
                    self.on_text_change(self)

        # 普通字符
        elif 32 <= key <= 126:
            if len(self.text) < self.max_length:
                char = chr(key)
                self.text = self.text[:self.cursor_position] + char + self.text[self.cursor_position:]
                self.cursor_position += 1
                if self.on_text_change:
                    self.on_text_change(self)

    def handle_mouse_event(self, event: int, x: int, y: int, flags: int, param):
        if not self.visible or not self.enabled:
            return False

        is_inside = self.contains_point(x, y)

        # 处理点击获取焦点
        if event == cv2.EVENT_LBUTTONDOWN:
            if is_inside:
                self.is_focused = True
                self.cursor_position = len(self.text)  # 光标移到末尾
                Object.set_focus(self)
                return True
            else:
                self.is_focused = False
                Object.set_focus(None)

        return super().handle_mouse_event(event, x, y, flags, param)

    def on_blur(self):
        """失去焦点时的回调"""
        self.is_focused = False
        self.cursor_visible = True
        self.cursor_blink_time = 0

    def handle_key(self, key: int, is_press: bool = True) -> bool:
        """
        处理键盘输入

        Args:
            key: 键码
            is_press: True表示按下，False表示释放
        """
        if not self.is_focused or not self.enabled:
            return False

        # 按键释放
        if not is_press:
            if self.current_key == key:
                self.current_key = None
                # 如果释放的是左右箭头，检查是否停止移动
                if key in [2, 3]:
                    import time
                    current_time = time.time()
                    if current_time - self.last_cursor_move_time >= self.cursor_move_timeout:
                        self.cursor_moving = False
                        self.cursor_blink_time = 0
                        self.cursor_visible = True
            return True

        # 按键按下
        import time

        # Enter
        if key == 13:
            self.is_focused = False
            Object.set_focus(None)
            self.current_key = None
            return True

        # ESC
        elif key == 27:
            self.is_focused = False
            Object.set_focus(None)
            self.current_key = None
            return True

        # Home键 - 移到开头（不重复）
        elif key == 1:
            self.cursor_position = 0
            return True

        # End键 - 移到末尾（不重复）
        elif key == 4:
            self.cursor_position = len(self.text)
            return True

        # 可重复的按键
        elif key in [8, 2, 3, 127] or (32 <= key <= 126):
            # 首次按下立即执行
            self._process_key_action(key)

            # 记录按键状态用于长按重复
            self.current_key = key
            self.key_press_time = time.time()
            self.last_repeat_time = time.time()
            self.key_just_pressed = True
            return True

        return False

    def update(self, dt: float = 0):
        """更新光标闪烁和按键重复"""
        super().update(dt)

        import time
        current_time = time.time()

        # 检查光标是否停止移动
        if self.cursor_moving:
            if current_time - self.last_cursor_move_time >= self.cursor_move_timeout:
                self.cursor_moving = False
                # 停止移动后重置闪烁状态
                self.cursor_blink_time = 0
                self.cursor_visible = True

        # 光标闪烁（仅在不移动时闪烁）
        if self.is_focused and dt > 0:
            if self.cursor_moving:
                # 快速移动时常亮
                self.cursor_visible = True
                self.cursor_blink_time = 0
            else:
                # 静止时闪烁
                self.cursor_blink_time += dt
                if self.cursor_blink_time >= self.cursor_blink_interval:
                    self.cursor_visible = not self.cursor_visible
                    self.cursor_blink_time = 0

        # 按键长按重复
        if self.current_key is not None and self.is_focused:
            # 跳过刚按下的瞬间
            if self.key_just_pressed:
                self.key_just_pressed = False
                return

            # 首次重复需要等待 delay
            if current_time - self.key_press_time >= self.key_repeat_delay:
                # 之后按 interval 重复
                if current_time - self.last_repeat_time >= self.key_repeat_interval:
                    self._process_key_action(self.current_key)
                    self.last_repeat_time = current_time

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
            # 计算光标位置
            text_before_cursor = display_text[:self.cursor_position] if self.cursor_position <= len(
                display_text) else display_text
            cursor_offset = cv2.getTextSize(text_before_cursor, self.font, self.font_scale, self.font_thickness)[0][0]
            cursor_x = text_x + cursor_offset
            cv2.line(canvas, (cursor_x, ay + 8), (cursor_x, ay + self.height - 8),
                     self.text_color, 2)

        # 绘制子对象
        for child in self.children:
            child.draw(canvas)
