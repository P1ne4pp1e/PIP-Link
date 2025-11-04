import cv2
import numpy as np
from typing import Tuple, Optional, Callable
from ui_components.base_object import Object


class Label(Object):
    """文本标签组件"""

    def __init__(self, x: int, y: int, width: int, height: int, text: str = "", name: str = ""):
        super().__init__(x, y, width, height, name or "label")
        self.text = text
        self.text_color = (0, 0, 0)
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.5
        self.font_thickness = 1
        self.align = "left"  # left, center, right
        self.valign = "center"  # top, center, bottom

        # 默认透明背景
        self.background_color = (255, 255, 255)
        self.border_width = 0

    def draw(self, canvas: np.ndarray):
        if not self.visible:
            return

        ax, ay = self.absolute_position

        # 绘制背景
        if self.alpha < 1.0:
            overlay = canvas.copy()
            cv2.rectangle(overlay, (ax, ay),
                          (ax + self.width, ay + self.height),
                          self.background_color, -1)
            cv2.addWeighted(overlay, self.alpha, canvas, 1 - self.alpha, 0, canvas)
        else:
            cv2.rectangle(canvas, (ax, ay),
                          (ax + self.width, ay + self.height),
                          self.background_color, -1)

        # 绘制边框
        if self.border_width > 0:
            cv2.rectangle(canvas, (ax, ay),
                          (ax + self.width, ay + self.height),
                          self.border_color, self.border_width)

        # 绘制文本
        if self.text:
            text_size = cv2.getTextSize(self.text, self.font, self.font_scale, self.font_thickness)[0]

            # 水平对齐
            if self.align == "center":
                text_x = ax + (self.width - text_size[0]) // 2
            elif self.align == "right":
                text_x = ax + self.width - text_size[0] - 5
            else:  # left
                text_x = ax + 5

            # 垂直对齐
            if self.valign == "center":
                text_y = ay + (self.height + text_size[1]) // 2
            elif self.valign == "bottom":
                text_y = ay + self.height - 5
            else:  # top
                text_y = ay + text_size[1] + 5

            cv2.putText(canvas, self.text, (text_x, text_y),
                        self.font, self.font_scale, self.text_color, self.font_thickness)

        # 绘制子对象
        for child in self.children:
            child.draw(canvas)
