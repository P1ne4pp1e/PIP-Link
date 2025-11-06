import cv2
import numpy as np
import time
from core.config import Config
from core.state import AppState
from utils.events import EventBus, Events
from network.manager import NetworkManager
from ui.manager import UIManager
from mouse_tracker import MouseTracker


class ApplicationController:
    """应用主控制器"""

    def __init__(self):
        self.window_name = Config.WINDOW_NAME

        # 核心组件
        self.state = AppState()
        self.event_bus = EventBus()
        self.network = NetworkManager(self.state, self.event_bus)
        self.ui = UIManager(self.state, self.event_bus)

        # 鼠标追踪
        self.mouse_tracker = MouseTracker(on_move=self.on_mouse_move, poll_interval=0.001)

        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """设置事件处理"""
        # Connection Tab
        self.ui.connection_tab.connect_button.on_click = self._on_connect_click

        # Stream Tab
        self.ui.stream_tab.apply_button.on_click = self._on_apply_quality_click

        # Display Tab - 按钮已在__init__中创建，可以直接绑定
        self.ui.display_tab.windowed_btn.on_click = lambda obj: self._set_window_mode("windowed")
        self.ui.display_tab.fullscreen_btn.on_click = lambda obj: self._set_window_mode("fullscreen")

        # 分辨率按钮也已预创建
        for idx, btn in enumerate(self.ui.display_tab.resolution_buttons):
            btn.on_click = lambda obj, i=idx: self._set_resolution(i)

        # Image Tab
        self.ui.image_tab.apply_button.on_click = self._on_apply_image_click
        self.ui.image_tab.reset_button.on_click = self._on_reset_image_click

        # 让UIManager能访问network
        self.ui.set_network_manager(self.network)

    def _on_connect_click(self, obj):
        """连接按钮点击"""
        if self.state.connection.is_connected:
            self.network.disconnect()
        else:
            values = self.ui.connection_tab.get_input_values()
            if values['ip'] and values['port']:
                try:
                    port = int(values['port'])
                    self.network.connect(values['ip'], port)
                except ValueError:
                    print("Invalid port")

    def _on_apply_quality_click(self, obj):
        """应用质量设置"""
        if not self.state.connection.is_connected:
            return

        values = self.ui.stream_tab.get_input_values()
        if values:
            self.network.send_quality_settings(
                values['jpeg_quality'],
                values['frame_scale']
            )

    def _on_apply_image_click(self, obj):
        """应用图像调整"""
        if not self.state.connection.is_connected:
            return

        values = self.ui.image_tab.get_input_values()
        if values:
            self.network.send_image_adjustment(
                values['exposure'],
                values['contrast'],
                values['gamma']
            )

    def _on_reset_image_click(self, obj):
        """重置图像调整"""
        if not self.state.connection.is_connected:
            return

        self.network.send_image_adjustment(1.0, 1.0, 1.0)

        # 更新UI显示
        self.ui.image_tab.exposure_textbox.text = "1.00"
        self.ui.image_tab.contrast_textbox.text = "1.00"
        self.ui.image_tab.gamma_textbox.text = "1.00"

    def _set_window_mode(self, mode: str):
        """设置窗口模式"""
        self.state.ui.window_mode = mode

        if mode == "fullscreen":
            # 保存当前窗口大小
            self.saved_width = self.ui.width
            self.saved_height = self.ui.height

            # 切换到全屏
            cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

            # 获取屏幕分辨率
            import tkinter as tk
            root_tk = tk.Tk()
            width = root_tk.winfo_screenwidth()
            height = root_tk.winfo_screenheight()
            root_tk.destroy()

            self.ui.resize(width, height)
        else:
            # 切换回窗口模式
            cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
            # 恢复之前的窗口大小
            if hasattr(self, 'saved_width'):
                width = self.saved_width
                height = self.saved_height
            else:
                width = Config.DEFAULT_WIDTH
                height = Config.DEFAULT_HEIGHT

            cv2.resizeWindow(self.window_name, width, height)
            self.ui.resize(width, height)

            # 刷新Display选项卡
        self.ui.debug_panel._rebuild_content()

    def _set_resolution(self, index: int):
        """设置分辨率"""
        if self.state.ui.window_mode != "windowed":
            return

        self.state.ui.current_resolution_index = index
        res_name, (new_width, new_height) = Config.AVAILABLE_RESOLUTIONS[index]

        # 调整窗口
        cv2.resizeWindow(self.window_name, new_width, new_height)
        self.ui.resize(new_width, new_height)

        print(f"[Display] Resolution changed to {res_name}")
        self.ui.debug_panel._rebuild_content()

    def _handle_key(self, key: int) -> bool:
        """处理按键"""
        if key == 27:  # ESC
            # 先检查是否有TextBox聚焦
            from ui.components.base_object import Object
            focused = Object.get_focused_object()
            if focused and hasattr(focused, 'is_focused'):
                focused.is_focused = False
                Object.set_focus(None)
            else:
                self.ui.toggle_debug_panel()
            return True

        # 收集所有TextBox
        textboxes = [
            self.ui.connection_tab.ip_textbox,
            self.ui.connection_tab.port_textbox,
            self.ui.stream_tab.jpeg_quality_textbox,
            self.ui.stream_tab.frame_scale_textbox,
            self.ui.image_tab.exposure_textbox,
            self.ui.image_tab.contrast_textbox,
            self.ui.image_tab.gamma_textbox,
        ]

        for tb in textboxes:
            if tb.handle_key(key):
                return True

        return True

    def on_mouse_move(self, x, y):
        """鼠标移动"""
        if self.network.control and self.state.control.state == 1:
            current_time = time.time()
            dt = current_time - getattr(self, 'last_mouse_time', current_time)
            self.last_mouse_time = current_time
            self.network.control.update_mouse_position(x, y, dt)

    def run(self):
        """主循环"""
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, self.ui.width, self.ui.height)
        cv2.setMouseCallback(self.window_name, self.ui.handle_mouse_event)

        self.mouse_tracker.start()

        last_time = time.time()

        while True:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time

            # 创建画布
            canvas = self._create_canvas()

            # 更新和绘制
            self.ui.update(dt)
            self.ui.draw(canvas)

            # 显示
            cv2.imshow(self.window_name, canvas)

            # 按键处理
            key = cv2.waitKey(1)
            if not self._handle_key(key):
                break

            if cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1:
                break

        self._cleanup()

    def _create_canvas(self) -> np.ndarray:
        """创建画布"""
        if self.state.video.video_frame is not None:
            frame = self.state.video.video_frame.copy()
            frame_h, frame_w = frame.shape[:2]
            scale = min(self.ui.width / frame_w, self.ui.height / frame_h)
            new_w = int(frame_w * scale)
            new_h = int(frame_h * scale)
            resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

            canvas = np.zeros((self.ui.height, self.ui.width, 3), dtype=np.uint8)
            x_offset = (self.ui.width - new_w) // 2
            y_offset = (self.ui.height - new_h) // 2
            canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized
        else:
            canvas = np.zeros((self.ui.height, self.ui.width, 3), dtype=np.uint8)
            canvas[:] = (30, 30, 30)

        return canvas

    def _handle_key(self, key: int) -> bool:
        """处理按键"""
        if key == 27:  # ESC
            self.ui.toggle_debug_panel()

        # 让TextBox处理按键
        textboxes = [
            self.ui.connection_tab.ip_textbox,
            self.ui.connection_tab.port_textbox,
            self.ui.stream_tab.jpeg_quality_textbox,
            self.ui.stream_tab.frame_scale_textbox,
        ]

        for tb in textboxes:
            if tb.handle_key(key):
                return True

        return True

    def _cleanup(self):
        """清理资源"""
        self.network.disconnect()
        self.mouse_tracker.stop()
        cv2.destroyAllWindows()