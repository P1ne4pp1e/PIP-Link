"""
选项卡式 Debug 面板
支持多个选项卡，每个选项卡显示不同的内容
"""

import cv2
import numpy as np
from typing import List, Optional, Callable
from ui_components.base_object import Object
from ui_components.label import Label


class Tab:
    """选项卡"""

    def __init__(self, name: str, content_builder: Callable):
        self.name = name
        self.content_builder = content_builder  # 返回 UI 组件列表的函数
        self.is_active = False


class TabbedPanel(Object):
    """选项卡面板"""

    def __init__(self, x: int, y: int, width: int, height: int, name: str = ""):
        super().__init__(x, y, width, height, name or "tabbed_panel")

        # 面板样式
        self.background_color = (45, 45, 52)
        self.border_color = (70, 130, 180)
        self.border_width = 2
        self.alpha = 0.95

        # 选项卡样式
        self.tab_height = 35
        self.tab_spacing = 2
        self.active_tab_color = (70, 130, 180)
        self.inactive_tab_color = (55, 55, 62)
        self.tab_text_color = (240, 240, 245)
        self.tab_inactive_text_color = (160, 160, 170)

        # 内容区域
        self.content_padding = 12
        self.content_y = self.tab_height + 5

        # 选项卡列表
        self.tabs: List[Tab] = []
        self.active_tab_index = 0

        # 选项卡按钮区域
        self.tab_buttons = []

        # 内容容器
        self.content_container = Object(
            self.content_padding,
            self.content_y,
            self.width - self.content_padding * 2,
            self.height - self.content_y - self.content_padding,
            "content_container"
        )
        self.content_container.background_color = (45, 45, 52)
        self.add_child(self.content_container)

    def add_tab(self, name: str, content_builder: Callable):
        """
        添加选项卡

        Args:
            name: 选项卡名称
            content_builder: 内容构建函数，返回 UI 组件列表
        """
        tab = Tab(name, content_builder)
        self.tabs.append(tab)

        # 第一个选项卡默认激活
        if len(self.tabs) == 1:
            tab.is_active = True
            self.active_tab_index = 0
            self._rebuild_content()

    def switch_tab(self, index: int):
        """切换选项卡"""
        if 0 <= index < len(self.tabs):
            # 取消所有选项卡的激活状态
            for tab in self.tabs:
                tab.is_active = False

            # 激活指定选项卡
            self.tabs[index].is_active = True
            self.active_tab_index = index

            # 重建内容
            self._rebuild_content()

    def _rebuild_content(self):
        """重建当前选项卡的内容"""
        # 清空内容容器
        self.content_container.children.clear()

        # 获取当前激活的选项卡
        if 0 <= self.active_tab_index < len(self.tabs):
            active_tab = self.tabs[self.active_tab_index]

            # 调用内容构建函数
            content_items = active_tab.content_builder()

            # 添加内容到容器
            for item in content_items:
                self.content_container.add_child(item)

    def handle_mouse_event(self, event: int, x: int, y: int, flags: int, param):
        """处理鼠标事件"""
        if not self.visible or not self.enabled:
            return False

        # 先让子对象处理
        for child in reversed(self.children):
            if child.handle_mouse_event(event, x, y, flags, param):
                return True

        # 检查是否点击了选项卡
        if event == cv2.EVENT_LBUTTONDOWN:
            ax, ay = self.absolute_position

            # 计算每个选项卡的宽度
            if len(self.tabs) > 0:
                tab_width = (self.width - (len(self.tabs) - 1) * self.tab_spacing) // len(self.tabs)

                for i, tab in enumerate(self.tabs):
                    tab_x = ax + i * (tab_width + self.tab_spacing)
                    tab_y = ay

                    if (tab_x <= x <= tab_x + tab_width and
                            tab_y <= y <= tab_y + self.tab_height):
                        self.switch_tab(i)
                        return True

        return super().handle_mouse_event(event, x, y, flags, param)

    def draw(self, canvas: np.ndarray):
        """绘制面板"""
        if not self.visible:
            return

        ax, ay = self.absolute_position

        # 绘制主背景（带透明度）
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

        # 绘制选项卡
        self._draw_tabs(canvas, ax, ay)

        # 绘制边框
        if self.border_width > 0:
            cv2.rectangle(canvas, (ax, ay),
                          (ax + self.width, ay + self.height),
                          self.border_color, self.border_width)

        # 绘制内容容器
        for child in self.children:
            child.draw(canvas)

    def _draw_tabs(self, canvas: np.ndarray, x: int, y: int):
        """绘制选项卡栏"""
        if len(self.tabs) == 0:
            return

        # 计算每个选项卡的宽度
        tab_width = (self.width - (len(self.tabs) - 1) * self.tab_spacing) // len(self.tabs)

        for i, tab in enumerate(self.tabs):
            tab_x = x + i * (tab_width + self.tab_spacing)
            tab_y = y

            # 选项卡背景颜色
            if tab.is_active:
                tab_color = self.active_tab_color
                text_color = self.tab_text_color
            else:
                tab_color = self.inactive_tab_color
                text_color = self.tab_inactive_text_color

            # 绘制选项卡背景
            cv2.rectangle(canvas, (tab_x, tab_y),
                          (tab_x + tab_width, tab_y + self.tab_height),
                          tab_color, -1)

            # 绘制选项卡边框
            if tab.is_active:
                cv2.rectangle(canvas, (tab_x, tab_y),
                              (tab_x + tab_width, tab_y + self.tab_height),
                              self.border_color, 2)

            # 绘制选项卡文本（居中）
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            font_thickness = 1 if not tab.is_active else 2

            text_size = cv2.getTextSize(tab.name, font, font_scale, font_thickness)[0]
            text_x = tab_x + (tab_width - text_size[0]) // 2
            text_y = tab_y + (self.tab_height + text_size[1]) // 2

            cv2.putText(canvas, tab.name, (text_x, text_y),
                        font, font_scale, text_color, font_thickness)


# ==================== 测试代码 ====================
if __name__ == '__main__':
    import time


    def create_connection_content():
        """连接信息内容"""
        items = []

        # IP 地址标签
        label1 = Label(10, 10, 300, 25, "Server IP: 192.168.1.100", "ip_label")
        label1.text_color = (200, 200, 200)
        label1.font_scale = 0.5
        label1.align = "left"
        items.append(label1)

        # 端口标签
        label2 = Label(10, 40, 300, 25, "Port: 8888", "port_label")
        label2.text_color = (200, 200, 200)
        label2.font_scale = 0.5
        label2.align = "left"
        items.append(label2)

        # 状态标签
        label3 = Label(10, 70, 300, 25, "Status: Connected", "status_label")
        label3.text_color = (100, 255, 100)
        label3.font_scale = 0.5
        label3.align = "left"
        items.append(label3)

        return items


    def create_stream_params_content():
        """流参数内容"""
        items = []

        label1 = Label(10, 10, 300, 25, "JPEG Quality: 80%", "quality_label")
        label1.text_color = (200, 200, 200)
        label1.font_scale = 0.5
        label1.align = "left"
        items.append(label1)

        label2 = Label(10, 40, 300, 25, "Frame Scale: 1.0x", "scale_label")
        label2.text_color = (200, 200, 200)
        label2.font_scale = 0.5
        label2.align = "left"
        items.append(label2)

        label3 = Label(10, 70, 300, 25, "Target FPS: 30", "fps_label")
        label3.text_color = (200, 200, 200)
        label3.font_scale = 0.5
        label3.align = "left"
        items.append(label3)

        return items


    def create_statistics_content():
        """统计信息内容"""
        items = []

        label1 = Label(10, 10, 300, 25, "Frames Received: 1024", "frames_label")
        label1.text_color = (200, 200, 200)
        label1.font_scale = 0.5
        label1.align = "left"
        items.append(label1)

        label2 = Label(10, 40, 300, 25, "Latency: 15ms", "latency_label")
        label2.text_color = (100, 255, 100)
        label2.font_scale = 0.5
        label2.align = "left"
        items.append(label2)

        return items


    # 创建窗口
    width, height = 800, 600
    window_name = "Tabbed Panel Test"

    # 创建根对象
    root = Object(0, 0, width, height, "root")
    root.background_color = (30, 30, 30)

    # 创建选项卡面板
    panel = TabbedPanel(50, 50, 400, 300, "debug_panel")
    panel.add_tab("Connection", create_connection_content)
    panel.add_tab("Stream", create_stream_params_content)
    panel.add_tab("Statistics", create_statistics_content)
    root.add_child(panel)


    # 鼠标回调
    def mouse_callback(event, x, y, flags, param):
        root.handle_mouse_event(event, x, y, flags, param)


    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, mouse_callback)

    last_time = time.time()

    while True:
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time

        # 创建画布
        canvas = np.zeros((height, width, 3), dtype=np.uint8)
        canvas[:] = root.background_color

        # 更新和绘制
        root.update(dt)
        root.draw(canvas)

        cv2.imshow(window_name, canvas)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break

        # 检查窗口是否关闭
        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            break

    cv2.destroyAllWindows()