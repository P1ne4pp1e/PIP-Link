"""
状态指示器 - 左下角动画显示
"""

import cv2
import numpy as np
import time


class StateIndicator:
    """状态指示器"""

    def __init__(self, x: int, y: int):
        """
        初始化状态指示器

        Args:
            x: 左下角X坐标
            y: 左下角Y坐标 (注意是底部坐标)
        """
        self.x = x
        self.y = y
        self.text = "Not Ready"
        self.color = (100, 100, 255)  # 橙红色

        # 动画参数
        self.animation_progress = 0.0
        self.animation_duration = 0.4
        self.is_animating = False
        self.animation_start_time = 0

        # 呼吸灯效果
        self.breath_time = 0.0

    def trigger_animation(self, new_text: str, new_color: tuple):
        """触发切换动画"""
        self.text = new_text
        self.color = new_color
        self.animation_progress = 0.0
        self.is_animating = True
        self.animation_start_time = time.time()
        # ===== 新增：重置呼吸灯 =====
        self.breath_time = 0.0

    def update(self, dt: float):
        """更新动画"""
        if self.is_animating:
            elapsed = time.time() - self.animation_start_time
            self.animation_progress = elapsed / self.animation_duration

            if self.animation_progress >= 1.0:
                self.animation_progress = 1.0
                self.is_animating = False

        # 更新呼吸灯时间
        self.breath_time += dt

    def draw(self, canvas: np.ndarray):
        """绘制状态指示器"""
        # 缩放动画: 0.85 -> 1.3 -> 1.0
        if self.is_animating:
            scale = 0.85 + 0.45 * np.sin(self.animation_progress * np.pi)
        else:
            scale = 1.0

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7 * scale
        thickness = 2

        # 计算文本大小
        text_size = cv2.getTextSize(self.text, font, font_scale, thickness)[0]
        padding = 15

        bg_width = text_size[0] + padding * 3 + 30  # 额外空间给指示灯
        bg_height = text_size[1] + padding * 2

        # 背景位置 (从左下角向上)
        bg_x = self.x
        bg_y = self.y - bg_height

        # 绘制半透明背景
        overlay = canvas.copy()
        cv2.rectangle(overlay,
                      (bg_x, bg_y),
                      (bg_x + bg_width, self.y),
                      (30, 30, 35), -1)
        cv2.addWeighted(overlay, 0.85, canvas, 0.15, 0, canvas)

        # 绘制边框
        cv2.rectangle(canvas,
                      (bg_x, bg_y),
                      (bg_x + bg_width, self.y),
                      self.color, 2)

        # 绘制文本
        text_x = bg_x + padding
        text_y = self.y - padding
        cv2.putText(canvas, self.text, (text_x, text_y),
                    font, font_scale, self.color, thickness, cv2.LINE_AA)

        # 绘制状态指示灯
        indicator_radius = 7
        indicator_x = bg_x + bg_width - 20
        indicator_y = bg_y + bg_height // 2

        if self.text == "Ready":
            # Ready: 绿色呼吸灯
            breath_alpha = 0.5 + 0.5 * np.sin(self.breath_time * 4)
            glow_color = (0, int(255 * breath_alpha), 0)

            # 外圈光晕
            cv2.circle(canvas, (indicator_x, indicator_y),
                       int(indicator_radius * 1.5), glow_color, -1)
            # 内圈
            cv2.circle(canvas, (indicator_x, indicator_y),
                       indicator_radius, (0, 255, 0), -1)
        else:
            # Not Ready: 红色静态灯
            cv2.circle(canvas, (indicator_x, indicator_y),
                       indicator_radius, self.color, -1)
            # 边框
            cv2.circle(canvas, (indicator_x, indicator_y),
                       indicator_radius, (200, 200, 200), 1)