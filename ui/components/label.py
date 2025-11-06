import cv2
import numpy as np
from ui.components.base_object import Object


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

        # 绘制文本 - 支持多行
        if self.text:
            lines = self.text.split('\n')
            line_height = cv2.getTextSize('A', self.font, self.font_scale, self.font_thickness)[0][1] + 5

            # 计算总文本高度
            total_text_height = len(lines) * line_height

            # 根据垂直对齐计算起始y坐标
            if self.valign == "center":
                start_y = ay + (self.height - total_text_height) // 2 + line_height
            elif self.valign == "bottom":
                start_y = ay + self.height - total_text_height
            else:  # top
                start_y = ay + line_height

            # 绘制每一行
            for i, line in enumerate(lines):
                if not line:  # 跳过空行但保留行距
                    continue

                text_size = cv2.getTextSize(line, self.font, self.font_scale, self.font_thickness)[0]

                # 水平对齐
                if self.align == "center":
                    text_x = ax + (self.width - text_size[0]) // 2
                elif self.align == "right":
                    text_x = ax + self.width - text_size[0] - 5
                else:  # left
                    text_x = ax + 5

                text_y = start_y + i * line_height

                cv2.putText(canvas, line, (text_x, text_y),
                            self.font, self.font_scale, self.text_color, self.font_thickness)

        # 绘制子对象
        for child in self.children:
            child.draw(canvas)