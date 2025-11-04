import numpy as np
import cv2
import time
import threading
from ui_components.base_object import Object
from ui_components.panel import Panel
from ui_components.label import Label
from ui_components.textbox import TextBox
from ui_components.button import Button
from web_conn.tcp_conn import TCPConnection
from web_conn.udp_conn import UDPReceiver


class PIPLinkApp:
    def __init__(self):
        self.window_name = 'PIP-Link'
        self.width = 1024
        self.height = 768

        # 连接信息
        self.server_ip = ""
        self.server_port = ""
        self.is_connected = False
        self.udp_port = 9999  # 默认值

        # TCP 连接管理器
        self.tcp_conn = TCPConnection(timeout=5)
        self.tcp_conn.udp_port = self.udp_port  # 设置 UDP 端口
        self.setup_tcp_callbacks()

        # UDP 接收器
        self.udp_receiver = None

        # UI 可见性控制
        self.debug_panel_visible = True

        # 视频帧
        self.video_frame = None
        self.video_frame_lock = threading.Lock()

        # 初始化UI
        self.setup_ui()

    def setup_ui(self):
        """初始化UI组件"""
        # 根对象
        self.root = Object(0, 0, self.width, self.height, "root")
        self.root.background_color = (30, 30, 30)

        # ===== 左上角调试面板 =====
        panel_width = 360
        panel_height = 320

        self.debug_panel = Panel(20, 20, panel_width, panel_height, "debug_panel")
        self.debug_panel.title = "Connection & Debug"
        self.debug_panel.background_color = (50, 50, 55, 230)
        self.debug_panel.alpha = 0.95
        self.debug_panel.title_color = (70, 130, 180)
        self.debug_panel.border_color = (70, 130, 180)
        self.debug_panel.border_width = 2
        self.root.add_child(self.debug_panel)

        # 连接状态指示器
        self.connection_status = Label(20, 50, 320, 25, "Status: Disconnected", "status_indicator")
        self.connection_status.text_color = (255, 100, 100)
        self.connection_status.font_scale = 0.5
        self.connection_status.font_thickness = 2
        self.connection_status.background_color = (50, 50, 55)
        self.connection_status.align = "left"
        self.debug_panel.add_child(self.connection_status)

        # IP地址标签
        ip_label = Label(20, 85, 320, 20, "Server IP:", "ip_label")
        ip_label.text_color = (200, 200, 200)
        ip_label.font_scale = 0.45
        ip_label.background_color = (50, 50, 55)
        ip_label.align = "left"
        self.debug_panel.add_child(ip_label)

        # IP地址输入框
        self.ip_textbox = TextBox(20, 110, 320, 36, "ip_textbox")
        self.ip_textbox.placeholder = "192.168.1.100"
        self.ip_textbox.max_length = 15
        self.ip_textbox.font_scale = 0.5
        self.ip_textbox.on_text_change = self.on_ip_change
        self.debug_panel.add_child(self.ip_textbox)

        # 端口号标签
        port_label = Label(20, 155, 320, 20, "Port:", "port_label")
        port_label.text_color = (200, 200, 200)
        port_label.font_scale = 0.45
        port_label.background_color = (50, 50, 55)
        port_label.align = "left"
        self.debug_panel.add_child(port_label)

        # 端口号输入框
        self.port_textbox = TextBox(20, 180, 320, 36, "port_textbox")
        self.port_textbox.placeholder = "8888"
        self.port_textbox.max_length = 5
        self.port_textbox.font_scale = 0.5
        self.port_textbox.on_text_change = self.on_port_change
        self.debug_panel.add_child(self.port_textbox)

        # 连接/断开按钮
        self.connect_button = Button(20, 230, 320, 40, "Connect", "connect_btn")
        self.connect_button.background_color = (70, 130, 180)
        self.connect_button.hover_color = (90, 150, 200)
        self.connect_button.pressed_color = (50, 110, 160)
        self.connect_button.font_scale = 0.6
        self.connect_button.on_click = self.on_connect_click
        self.debug_panel.add_child(self.connect_button)

        # 提示信息标签
        self.hint_label = Label(20, 280, 320, 30, "Press ESC to toggle panel", "hint_label")
        self.hint_label.text_color = (150, 150, 150)
        self.hint_label.font_scale = 0.4
        self.hint_label.align = "center"
        self.hint_label.background_color = (50, 50, 55)
        self.debug_panel.add_child(self.hint_label)

        # ===== 右下角信息显示 =====
        info_width = 300
        info_height = 80
        self.info_label = Label(self.width - info_width - 20, self.height - info_height - 20,
                                info_width, info_height, "No video stream", "info_display")
        self.info_label.text_color = (150, 150, 150)
        self.info_label.font_scale = 0.45
        self.info_label.align = "center"
        self.info_label.valign = "center"
        self.info_label.background_color = (40, 40, 45)
        self.info_label.alpha = 0.8
        self.info_label.border_color = (70, 70, 75)
        self.info_label.border_width = 1
        self.root.add_child(self.info_label)

    def on_ip_change(self, obj):
        """IP输入变化回调"""
        self.server_ip = obj.text

    def on_port_change(self, obj):
        """端口输入变化回调"""
        self.server_port = obj.text
        # 自动计算 UDP 端口 = TCP 端口 + 1
        try:
            tcp_port = int(obj.text) if obj.text else 8888
            self.udp_port = tcp_port + 1
            self.tcp_conn.udp_port = self.udp_port
            print(f"[INFO] TCP Port: {tcp_port}, UDP Port: {self.udp_port}")
        except ValueError:
            self.udp_port = 8889
            self.tcp_conn.udp_port = 8889

    def setup_tcp_callbacks(self):
        """设置TCP连接的回调函数"""
        self.tcp_conn.on_connecting = self.on_tcp_connecting
        self.tcp_conn.on_success = self.on_tcp_success
        self.tcp_conn.on_timeout = self.on_tcp_timeout
        self.tcp_conn.on_refused = self.on_tcp_refused
        self.tcp_conn.on_error = self.on_tcp_error

    def on_tcp_connecting(self):
        """TCP开始连接"""
        self.connection_status.text = "Status: Connecting..."
        self.connection_status.text_color = (255, 200, 100)

    def on_tcp_success(self):
        """TCP连接成功"""
        self.is_connected = True
        self.connect_button.text = "Disconnect"
        self.connect_button.background_color = (180, 70, 70)
        self.connection_status.text = "Status: Connected (TCP OK)"
        self.connection_status.text_color = (100, 255, 100)
        self.info_label.text = f"TCP handshake completed\n{self.server_ip}:{self.server_port}\nReady for UDP communication"

        # 启动 UDP 接收器
        self.start_udp_receiver()

    def on_tcp_timeout(self):
        """TCP连接超时"""
        self.connection_status.text = "Status: Connection Timeout"
        self.connection_status.text_color = (255, 100, 100)
        self.info_label.text = "Connection timeout\nCheck IP/Port and network"

    def on_tcp_refused(self):
        """TCP连接被拒绝"""
        self.connection_status.text = "Status: Connection Refused"
        self.connection_status.text_color = (255, 100, 100)
        self.info_label.text = "Connection refused\nServer may not be running"

    def on_tcp_error(self, error: Exception):
        """TCP连接错误"""
        self.connection_status.text = f"Status: Error - {type(error).__name__}"
        self.connection_status.text_color = (255, 100, 100)
        self.info_label.text = f"Connection failed\n{str(error)}"

    def on_connect_click(self, obj):
        """连接按钮点击回调"""
        if self.is_connected:
            # 断开连接
            self.is_connected = False
            self.tcp_conn.disconnect()
            self.stop_udp_receiver()
            self.connect_button.text = "Connect"
            self.connect_button.background_color = (70, 130, 180)
            self.connection_status.text = "Status: Disconnected"
            self.connection_status.text_color = (255, 100, 100)
            self.info_label.text = "Connection closed"
            print("[INFO] Connection closed by user")
            return

        # 验证输入
        if not self.server_ip or not self.server_port:
            self.connection_status.text = "Status: Missing IP or Port"
            self.connection_status.text_color = (255, 150, 50)
            return

        # 验证端口号格式
        try:
            port_num = int(self.server_port)
            if port_num < 1 or port_num > 65535:
                raise ValueError
        except ValueError:
            self.connection_status.text = "Status: Invalid Port (1-65535)"
            self.connection_status.text_color = (255, 150, 50)
            return

        # 发起TCP握手
        self.tcp_conn.handshake(self.server_ip, port_num, async_mode=True)

    def start_udp_receiver(self):
        """启动 UDP 接收器"""
        if self.udp_receiver is None:
            self.udp_receiver = UDPReceiver(self.udp_port)
            self.udp_receiver.on_frame_received = self.on_udp_frame_received
            self.udp_receiver.start()
            print(f"[INFO] UDP receiver started on port {self.udp_port}")

    def stop_udp_receiver(self):
        """停止 UDP 接收器"""
        if self.udp_receiver:
            self.udp_receiver.stop()
            self.udp_receiver = None
            print("[INFO] UDP receiver stopped")

    def on_udp_frame_received(self, frame: np.ndarray):
        """UDP 帧接收回调"""
        with self.video_frame_lock:
            self.video_frame = frame.copy()
            print(f"[DEBUG] 帧已接收: {frame.shape}, dtype: {frame.dtype}")

    def toggle_debug_panel(self):
        """切换调试面板的可见性"""
        self.debug_panel_visible = not self.debug_panel_visible
        self.debug_panel.visible = self.debug_panel_visible

    def mouse_callback(self, event, x, y, flags, param):
        """鼠标事件回调"""
        self.root.handle_mouse_event(event, x, y, flags, param)

    def run(self):
        """主循环"""
        cv2.namedWindow(self.window_name)
        cv2.resizeWindow(self.window_name, self.width, self.height)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)

        last_time = time.time()

        print("=== PIP-Link Started ===")
        print(f"Window Size: {self.width}x{self.height}")
        print("Press ESC to toggle debug panel")

        frame_count = 0

        while True:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time

            # 创建画布 - 直接用视频流作为背景
            if self.video_frame is not None:
                with self.video_frame_lock:
                    frame = self.video_frame.copy()

                # 缩放视频帧以适应窗口
                frame_h, frame_w = frame.shape[:2]
                scale = min(self.width / frame_w, self.height / frame_h)
                new_w = int(frame_w * scale)
                new_h = int(frame_h * scale)
                resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

                # 创建画布并填充视频
                canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
                x_offset = (self.width - new_w) // 2
                y_offset = (self.height - new_h) // 2
                canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized
            else:
                # 没有视频时显示灰色背景
                canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
                canvas[:] = self.root.background_color

            # 更新UI
            self.root.update(dt)

            # 绘制 UI 组件（调试面板等）
            self.root.draw(canvas)

            # 显示
            cv2.imshow(self.window_name, canvas)

            # 每 30 帧打印一次调试信息
            frame_count += 1
            if frame_count % 30 == 0:
                has_video = "✓" if self.video_frame is not None else "✗"
                print(f"[DEBUG] 帧数: {frame_count}, 有视频: {has_video}, "
                      f"总接收帧: {self.udp_receiver.total_frames_received if self.udp_receiver else 0}")

            # 按键处理
            key = cv2.waitKey(1) & 0xFF

            # ESC键切换调试面板
            if key == 27:
                focused = Object.get_focused_object()
                if focused and isinstance(focused, TextBox):
                    focused.is_focused = False
                    Object.set_focus(None)
                else:
                    self.toggle_debug_panel()
                continue

            # 让TextBox处理键盘输入
            if self.ip_textbox.handle_key(key) or self.port_textbox.handle_key(key):
                continue

            # 检查窗口是否关闭
            if cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1:
                break

        # 清理
        self.stop_udp_receiver()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    app = PIPLinkApp()
    app.run()