import cv2
import numpy as np
from ui.ui_components.base_object import Object

class Panel(Object):
    """面板容器组件"""

    def __init__(self, x: int, y: int, width: int, height: int, name: str = ""):
        super().__init__(x, y, width, height, name or "panel")
        self.background_color = (245, 245, 245)
        self.border_color = (180, 180, 180)
        self.border_width = 1

        # 面板标题
        self.title = ""
        self.title_height = 30
        self.title_color = (200, 200, 200)
        self.title_text_color = (50, 50, 50)

    def draw(self, canvas: np.ndarray):
        if not self.visible:
            return

        ax, ay = self.absolute_position

        # 绘制主体背景
        cv2.rectangle(canvas, (ax, ay),
                      (ax + self.width, ay + self.height),
                      self.background_color, -1)

        # 绘制标题栏
        if self.title:
            cv2.rectangle(canvas, (ax, ay),
                          (ax + self.width, ay + self.title_height),
                          self.title_color, -1)

            # 绘制标题文字
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            font_thickness = 1
            text_size = cv2.getTextSize(self.title, font, font_scale, font_thickness)[0]
            text_x = ax + 10
            text_y = ay + (self.title_height + text_size[1]) // 2
            cv2.putText(canvas, self.title, (text_x, text_y),
                        font, font_scale, self.title_text_color, font_thickness)

        # 绘制边框
        if self.border_width > 0:
            cv2.rectangle(canvas, (ax, ay),
                          (ax + self.width, ay + self.height),
                          self.border_color, self.border_width)

        # 绘制子对象
        for child in self.children:
            child.draw(canvas)
