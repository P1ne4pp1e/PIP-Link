import cv2
import numpy as np
from typing import Tuple, Optional, Callable
from ui_components.base_object import Object


class Button(Object):
    """按钮组件"""

    def __init__(self, x: int, y: int, width: int, height: int, text: str = "", name: str = ""):
        super().__init__(x, y, width, height, name or "button")
        self.text = text
        self.text_color = (255, 255, 255)
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.6
        self.font_thickness = 2

        # 按钮样式
        self.background_color = (70, 130, 180)
        self.hover_color = (100, 160, 210)
        self.pressed_color = (50, 100, 150)
        self.disabled_color = (150, 150, 150)
        self.border_width = 2
        self.border_color = (50, 100, 150)

    def draw(self, canvas: np.ndarray):
        if not self.visible:
            return

        ax, ay = self.absolute_position

        # 根据状态选择颜色
        if not self.enabled:
            color = self.disabled_color
        elif self.is_pressed:
            color = self.pressed_color
        elif self.is_hovered:
            color = self.hover_color
        else:
            color = self.background_color

        # 绘制背景
        cv2.rectangle(canvas, (ax, ay),
                      (ax + self.width, ay + self.height),
                      color, -1)

        # 绘制边框
        if self.border_width > 0:
            cv2.rectangle(canvas, (ax, ay),
                          (ax + self.width, ay + self.height),
                          self.border_color, self.border_width)

        # 绘制文本（居中）
        if self.text:
            text_size = cv2.getTextSize(self.text, self.font, self.font_scale, self.font_thickness)[0]
            text_x = ax + (self.width - text_size[0]) // 2
            text_y = ay + (self.height + text_size[1]) // 2
            cv2.putText(canvas, self.text, (text_x, text_y),
                        self.font, self.font_scale, self.text_color, self.font_thickness)

        # 绘制子对象
        for child in self.children:
            child.draw(canvas)