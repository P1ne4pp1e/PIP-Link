import numpy as np
import cv2
import time
import threading
from ui_components.base_object import Object
from ui_components.label import Label
from ui_components.textbox import TextBox
from ui_components.button import Button
from ui_components.tabbed_panel import TabbedPanel
from web_conn.tcp_conn import TCPConnection
from web_conn.udp_conn import UDPReceiver
from web_conn.params_receiver import ParamsReceiver


class PIPLinkApp:
    def __init__(self):
        self.window_name = 'PIP-Link'
        self.width = 1024
        self.height = 768

        # 连接信息
        self.server_ip = ""
        self.server_port = ""
        self.is_connected = False
        self.udp_port = 9999  # 视频流 UDP 端口 = TCP端口 + 1
        self.params_port = 10000  # 参数 UDP 端口 = TCP端口 + 2

        # TCP 连接管理器
        self.tcp_conn = TCPConnection(timeout=5)
        self.tcp_conn.udp_port = self.udp_port
        self.setup_tcp_callbacks()

        # UDP 接收器
        self.udp_receiver = None

        # 参数接收器
        self.params_receiver = None

        # UI 可见性控制
        self.debug_panel_visible = True

        # 视频帧
        self.video_frame = None
        self.video_frame_lock = threading.Lock()

        # 服务端参数
        self.server_params = None
        self.server_params_lock = threading.Lock()

        # 统计信息
        self.frames_received = 0
        self.latency_ms = 0.0
        self.last_param_time = 0

        # 连接状态更新计时器
        self.status_update_timer = 0
        self.status_update_interval = 0.5

        # UI 组件引用（避免重复创建）
        self.conn_status_label = None
        self.conn_duration_label = None

        # 初始化UI
        self.setup_ui()

    def setup_ui(self):
        """初始化UI组件"""
        # 根对象
        self.root = Object(0, 0, self.width, self.height, "root")
        self.root.background_color = (30, 30, 30)

        # ===== 选项卡式调试面板 =====
        panel_width = 420
        panel_height = 400

        self.debug_panel = TabbedPanel(20, 20, panel_width, panel_height, "debug_panel")
        self.root.add_child(self.debug_panel)

        # 添加选项卡
        self.debug_panel.add_tab("Connection", self.build_connection_tab)
        self.debug_panel.add_tab("Stream", self.build_stream_tab)
        self.debug_panel.add_tab("Clients", self.build_clients_tab)
        self.debug_panel.add_tab("Statistics", self.build_statistics_tab)

        # ===== 右下角信息显示 =====
        info_width = 300
        info_height = 60
        self.info_label = Label(self.width - info_width - 20, self.height - info_height - 20,
                                info_width, info_height, "Press ESC to toggle Debug Panel", "info_display")
        self.info_label.text_color = (150, 150, 150)
        self.info_label.font_scale = 0.4
        self.info_label.align = "center"
        self.info_label.valign = "center"
        self.info_label.background_color = (40, 40, 45)
        self.info_label.alpha = 0.8
        self.info_label.border_color = (70, 70, 75)
        self.info_label.border_width = 1
        self.root.add_child(self.info_label)

    # ===== 选项卡内容构建函数 =====

    def build_connection_tab(self):
        """构建连接选项卡"""
        items = []

        # 连接状态（只创建一次）
        if self.conn_status_label is None:
            self.conn_status_label = Label(10, 10, 380, 25, "Status: Disconnected", "conn_status")
            self.conn_status_label.text_color = (255, 100, 100)
            self.conn_status_label.background_color = (45, 45, 52)
            self.conn_status_label.font_scale = 0.5
            self.conn_status_label.font_thickness = 2
            self.conn_status_label.align = "left"
        items.append(self.conn_status_label)

        # 连接时长（只创建一次）
        if self.conn_duration_label is None:
            self.conn_duration_label = Label(10, 40, 380, 20, "Duration: --:--:--", "conn_duration")
            self.conn_duration_label.text_color = (200, 200, 200)
            self.conn_duration_label.background_color = (45, 45, 52)
            self.conn_duration_label.font_scale = 0.45
            self.conn_duration_label.font_thickness = 1
            self.conn_duration_label.align = "left"
        items.append(self.conn_duration_label)

        # IP 标签
        ip_label = Label(10, 70, 380, 20, "Server IP:", "ip_label")
        ip_label.text_color = (200, 200, 200)
        ip_label.background_color = (45, 45, 52)
        ip_label.font_scale = 0.45
        ip_label.font_thickness = 1
        ip_label.align = "left"
        items.append(ip_label)

        # IP 输入框
        self.ip_textbox = TextBox(10, 95, 380, 36, "ip_textbox")
        self.ip_textbox.placeholder = "192.168.1.100"
        self.ip_textbox.max_length = 15
        self.ip_textbox.font_scale = 0.5
        self.ip_textbox.on_text_change = self.on_ip_change
        items.append(self.ip_textbox)

        # 端口标签
        port_label = Label(10, 140, 380, 20, "Port:", "port_label")
        port_label.text_color = (200, 200, 200)
        port_label.background_color = (45, 45, 52)
        port_label.font_scale = 0.45
        port_label.font_thickness = 1
        port_label.align = "left"
        items.append(port_label)

        # 端口输入框
        self.port_textbox = TextBox(10, 165, 380, 36, "port_textbox")
        self.port_textbox.placeholder = "8888"
        self.port_textbox.max_length = 5
        self.port_textbox.font_scale = 0.5
        self.port_textbox.on_text_change = self.on_port_change
        items.append(self.port_textbox)

        # 连接按钮
        self.connect_button = Button(10, 215, 380, 40, "Connect", "connect_btn")
        self.connect_button.background_color = (70, 130, 180)
        self.connect_button.hover_color = (90, 150, 200)
        self.connect_button.pressed_color = (50, 110, 160)
        self.connect_button.font_scale = 0.6
        self.connect_button.on_click = self.on_connect_click
        items.append(self.connect_button)

        return items

    def build_stream_tab(self):
        """构建流参数选项卡"""
        items = []

        # 检查是否有服务端参数
        with self.server_params_lock:
            if self.server_params:
                stream, _ = self.server_params

                items.append(
                    self._create_param_label(10, 10, f"Resolution: {stream.resolution_w}x{stream.resolution_h}"))
                items.append(self._create_param_label(10, 40, f"JPEG Quality: {stream.jpeg_quality}%"))
                items.append(self._create_param_label(10, 70, f"Frame Scale: {stream.frame_scale:.0%}"))
                items.append(self._create_param_label(10, 100, f"Target FPS: {stream.target_fps}"))
                items.append(self._create_param_label(10, 130, f"Actual FPS: {stream.actual_fps:.1f}"))
            else:
                label = Label(10, 10, 380, 25, "No stream parameters received", "no_params")
                label.text_color = (150, 150, 150)
                label.background_color = (45, 45, 52)
                label.font_scale = 0.5
                label.font_thickness = 1
                label.align = "left"
                items.append(label)

        return items

    def build_clients_tab(self):
        """构建客户端列表选项卡"""
        items = []

        with self.server_params_lock:
            if self.server_params:
                _, clients = self.server_params

                if clients:
                    y_offset = 10
                    for idx, client in enumerate(clients, 1):
                        # 客户端标题
                        title = Label(10, y_offset, 380, 25, f"Client #{idx} (ID {client.client_id})",
                                      f"client_{idx}_title")
                        title.text_color = (100, 200, 255)
                        title.background_color = (45, 45, 52)
                        title.font_scale = 0.5
                        title.font_thickness = 2
                        title.align = "left"
                        items.append(title)
                        y_offset += 30

                        # TCP 信息
                        tcp_info = Label(20, y_offset, 360, 20, f"TCP: {client.ip}:{client.tcp_port}",
                                         f"client_{idx}_tcp")
                        tcp_info.text_color = (220, 220, 225)
                        tcp_info.background_color = (45, 45, 52)
                        tcp_info.font_scale = 0.45
                        tcp_info.font_thickness = 1
                        tcp_info.align = "left"
                        items.append(tcp_info)
                        y_offset += 25

                        # UDP 信息
                        udp_info = Label(20, y_offset, 360, 20, f"UDP: :{client.udp_port}", f"client_{idx}_udp")
                        udp_info.text_color = (220, 220, 225)
                        udp_info.background_color = (45, 45, 52)
                        udp_info.font_scale = 0.45
                        udp_info.font_thickness = 1
                        udp_info.align = "left"
                        items.append(udp_info)
                        y_offset += 25

                        # 连接时间
                        time_info = Label(20, y_offset, 360, 20, f"Connected: {client.connected_time}",
                                          f"client_{idx}_time")
                        time_info.text_color = (150, 150, 155)
                        time_info.background_color = (45, 45, 52)
                        time_info.font_scale = 0.4
                        time_info.font_thickness = 1
                        time_info.align = "left"
                        items.append(time_info)
                        y_offset += 35
                else:
                    label = Label(10, 10, 380, 25, "No clients connected", "no_clients")
                    label.text_color = (150, 150, 150)
                    label.background_color = (45, 45, 52)
                    label.font_scale = 0.5
                    label.font_thickness = 1
                    label.align = "left"
                    items.append(label)
            else:
                label = Label(10, 10, 380, 25, "No client data available", "no_data")
                label.text_color = (150, 150, 150)
                label.background_color = (45, 45, 52)
                label.font_scale = 0.5
                label.font_thickness = 1
                label.align = "left"
                items.append(label)

        return items

    def build_statistics_tab(self):
        """构建统计信息选项卡"""
        items = []

        # 接收帧数
        frames_label = Label(10, 10, 380, 25, f"Frames Received: {self.frames_received}", "frames_label")
        frames_label.text_color = (240, 240, 245)
        frames_label.background_color = (45, 45, 52)
        frames_label.font_scale = 0.5
        frames_label.font_thickness = 2
        frames_label.align = "left"
        items.append(frames_label)

        # 延迟
        latency_label = Label(10, 40, 380, 25, f"Network Latency: {self.latency_ms:.1f} ms", "latency_label")
        latency_label.text_color = (240, 240, 245)
        latency_label.background_color = (45, 45, 52)
        latency_label.font_scale = 0.5
        latency_label.font_thickness = 2
        latency_label.align = "left"
        items.append(latency_label)

        # 延迟状态
        latency_status = "Excellent" if self.latency_ms < 20 else "Good" if self.latency_ms < 50 else "Poor"
        latency_color = (100, 255, 100) if self.latency_ms < 20 else (220, 180, 50) if self.latency_ms < 50 else (255,
                                                                                                                  100,
                                                                                                                  100)

        status_label = Label(10, 70, 380, 25, f"Latency Status: {latency_status}", "latency_status")
        status_label.text_color = latency_color
        status_label.background_color = (45, 45, 52)
        status_label.font_scale = 0.5
        status_label.font_thickness = 2
        status_label.align = "left"
        items.append(status_label)

        # 参数更新时间
        time_since_update = time.time() - self.last_param_time if self.last_param_time > 0 else 999
        update_text = f"Last Update: {time_since_update:.1f}s ago" if time_since_update < 10 else "No recent updates"

        update_label = Label(10, 100, 380, 25, update_text, "last_update")
        update_label.text_color = (200, 200, 205)
        update_label.background_color = (45, 45, 52)
        update_label.font_scale = 0.45
        update_label.font_thickness = 1
        update_label.align = "left"
        items.append(update_label)

        return items

    def _create_param_label(self, x: int, y: int, text: str):
        """创建参数标签"""
        label = Label(x, y, 380, 25, text, f"param_{text[:10]}")
        label.text_color = (240, 240, 245)  # 更亮的浅色
        label.background_color = (45, 45, 52)  # 与面板背景一致
        label.font_scale = 0.5
        label.font_thickness = 2  # 加粗
        label.align = "left"
        return label

    def on_ip_change(self, obj):
        """IP输入变化回调"""
        self.server_ip = obj.text

    def on_port_change(self, obj):
        """端口输入变化回调"""
        self.server_port = obj.text
        try:
            tcp_port = int(obj.text) if obj.text else 8888
            self.udp_port = tcp_port + 1  # 视频流端口 = TCP + 1
            self.params_port = tcp_port + 2  # 参数端口 = TCP + 2
            self.tcp_conn.udp_port = self.udp_port
            print(f"[INFO] TCP Port: {tcp_port}, UDP Port: {self.udp_port}, Params Port: {self.params_port}")
        except ValueError:
            self.udp_port = 9999
            self.params_port = 10000
            self.tcp_conn.udp_port = 9999

    def setup_tcp_callbacks(self):
        """设置TCP连接的回调函数"""
        self.tcp_conn.on_connecting = self.on_tcp_connecting
        self.tcp_conn.on_success = self.on_tcp_success
        self.tcp_conn.on_timeout = self.on_tcp_timeout
        self.tcp_conn.on_refused = self.on_tcp_refused
        self.tcp_conn.on_error = self.on_tcp_error
        self.tcp_conn.on_disconnected = self.on_tcp_disconnected

    def on_tcp_connecting(self):
        """TCP开始连接"""
        if self.conn_status_label:
            self.conn_status_label.text = "Status: Connecting..."
            self.conn_status_label.text_color = (255, 200, 100)

    def on_tcp_success(self):
        """TCP连接成功"""
        self.is_connected = True
        self.connect_button.text = "Disconnect"
        self.connect_button.background_color = (180, 70, 70)

        if self.conn_status_label:
            self.conn_status_label.text = "Status: Connected"
            self.conn_status_label.text_color = (100, 255, 100)

        self.info_label.text = f"Connected to {self.server_ip}:{self.server_port}"

        # 启动 UDP 接收器
        self.start_udp_receiver()

        # 启动参数接收器
        self.start_params_receiver()

    def on_tcp_timeout(self):
        """TCP连接超时"""
        if self.conn_status_label:
            self.conn_status_label.text = "Status: Connection Timeout"
            self.conn_status_label.text_color = (255, 100, 100)
        self.info_label.text = "Connection timeout"
        self.stop_udp_receiver()
        self.stop_params_receiver()

    def on_tcp_refused(self):
        """TCP连接被拒绝"""
        if self.conn_status_label:
            self.conn_status_label.text = "Status: Connection Refused"
            self.conn_status_label.text_color = (255, 100, 100)
        self.info_label.text = "Connection refused"

    def on_tcp_error(self, error: Exception):
        """TCP连接错误"""
        if self.conn_status_label:
            self.conn_status_label.text = f"Status: Error"
            self.conn_status_label.text_color = (255, 100, 100)
        self.info_label.text = f"Connection failed: {type(error).__name__}"

    def on_tcp_disconnected(self):
        """TCP连接断开"""
        self.is_connected = False
        self.connect_button.text = "Connect"
        self.connect_button.background_color = (70, 130, 180)

        if self.conn_status_label:
            self.conn_status_label.text = "Status: Disconnected"
            self.conn_status_label.text_color = (255, 100, 100)

        if self.conn_duration_label:
            self.conn_duration_label.text = "Duration: --:--:--"

        self.info_label.text = "Connection lost"
        self.stop_udp_receiver()
        self.stop_params_receiver()

    def on_connect_click(self, obj):
        """连接按钮点击回调"""
        if self.is_connected:
            self.is_connected = False
            self.tcp_conn.disconnect()
            self.stop_udp_receiver()
            self.stop_params_receiver()
            self.connect_button.text = "Connect"
            self.connect_button.background_color = (70, 130, 180)

            if self.conn_status_label:
                self.conn_status_label.text = "Status: Disconnected"
                self.conn_status_label.text_color = (255, 100, 100)

            if self.conn_duration_label:
                self.conn_duration_label.text = "Duration: --:--:--"

            self.info_label.text = "Disconnected by user"
            return

        if not self.server_ip or not self.server_port:
            if self.conn_status_label:
                self.conn_status_label.text = "Status: Missing IP or Port"
                self.conn_status_label.text_color = (255, 150, 50)
            return

        try:
            port_num = int(self.server_port)
            if port_num < 1 or port_num > 65535:
                raise ValueError
        except ValueError:
            if self.conn_status_label:
                self.conn_status_label.text = "Status: Invalid Port"
                self.conn_status_label.text_color = (255, 150, 50)
            return

        self.tcp_conn.handshake(self.server_ip, port_num, async_mode=True)

    def start_udp_receiver(self):
        """启动 UDP 接收器"""
        if self.udp_receiver is None:
            self.udp_receiver = UDPReceiver(self.udp_port)
            self.udp_receiver.on_frame_received = self.on_udp_frame_received
            self.udp_receiver.start()

    def stop_udp_receiver(self):
        """停止 UDP 接收器"""
        if self.udp_receiver:
            self.udp_receiver.stop()
            self.udp_receiver = None

    def start_params_receiver(self):
        """启动参数接收器"""
        if self.params_receiver is None:
            self.params_receiver = ParamsReceiver(self.params_port)
            self.params_receiver.on_params_received = self.on_params_received
            self.params_receiver.start()
            print(f"[INFO] Params receiver started on port {self.params_port}")

    def stop_params_receiver(self):
        """停止参数接收器"""
        if self.params_receiver:
            self.params_receiver.stop()
            self.params_receiver = None

    def on_udp_frame_received(self, frame: np.ndarray):
        """UDP 帧接收回调"""
        with self.video_frame_lock:
            self.video_frame = frame.copy()
            self.frames_received += 1

    def on_params_received(self, stream_params, clients):
        """参数接收回调"""
        receive_time = time.time()  # 立即记录接收时间

        with self.server_params_lock:
            self.server_params = (stream_params, clients)

            # 计算延迟（使用单调时钟更精确）
            if stream_params.timestamp > 0:
                # 计算延迟：接收时间 - 发送时间
                latency = receive_time - stream_params.timestamp

                # 只有当延迟为正数且合理（< 5秒）时才更新
                if 0 < latency < 5.0:
                    self.latency_ms = latency * 1000
                else:
                    # 时间戳异常，可能是时钟不同步
                    if latency < 0:
                        print(
                            f"[WARNING] Negative latency detected: {latency * 1000:.1f}ms - clocks may not be synchronized")
                    self.latency_ms = 0.0

            self.last_param_time = receive_time

        # 刷新当前选项卡内容
        self.refresh_current_tab()

    def refresh_current_tab(self):
        """刷新当前选项卡的内容"""
        if self.debug_panel.visible:
            self.debug_panel._rebuild_content()

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

        while True:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time

            # 更新连接时长
            self.status_update_timer += dt
            if self.status_update_timer >= self.status_update_interval:
                if self.is_connected and self.conn_duration_label:
                    duration_str = self.tcp_conn.get_connection_time_str()
                    self.conn_duration_label.text = f"Duration: {duration_str}"
                self.status_update_timer = 0

            # 创建画布
            if self.video_frame is not None:
                with self.video_frame_lock:
                    frame = self.video_frame.copy()

                frame_h, frame_w = frame.shape[:2]
                scale = min(self.width / frame_w, self.height / frame_h)
                new_w = int(frame_w * scale)
                new_h = int(frame_h * scale)
                resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

                canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
                x_offset = (self.width - new_w) // 2
                y_offset = (self.height - new_h) // 2
                canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized
            else:
                canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
                canvas[:] = self.root.background_color

            # 更新UI
            self.root.update(dt)

            # 绘制 UI 组件
            self.root.draw(canvas)

            # 显示
            cv2.imshow(self.window_name, canvas)

            # 按键处理
            key = cv2.waitKey(1) & 0xFF

            if key == 27:  # ESC
                focused = Object.get_focused_object()
                if focused and isinstance(focused, TextBox):
                    focused.is_focused = False
                    Object.set_focus(None)
                else:
                    self.toggle_debug_panel()
                continue

            if self.ip_textbox.handle_key(key) or self.port_textbox.handle_key(key):
                continue

            if cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1:
                break

        # 清理
        self.stop_udp_receiver()
        self.stop_params_receiver()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    app = PIPLinkApp()
    app.run()