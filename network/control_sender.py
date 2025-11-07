"""
控制指令发送器 - 客户端
"""

import socket
import threading
import time
from network.control_packet import ControlPacket
from network.keyboard_encoder import KeyboardEncoder


class ControlSender:
    """控制指令发送器"""

    def __init__(self, target_rate: int = 100):
        """
        初始化控制发送器

        Args:
            target_rate: 目标发送频率 (Hz)
        """
        self.target_rate = target_rate
        self.send_interval = 1.0 / target_rate

        # 网络
        self.socket = None
        self.server_ip = ""
        self.control_port = 0

        # 状态
        self.state = 0  # 0=Not Ready, 1=Ready
        self.is_running = False
        self.send_thread = None

        # 鼠标状态
        self.last_mouse_dx = 0
        self.last_mouse_dy = 0
        self.mouse_velocity_x = 0.0
        self.mouse_velocity_y = 0.0
        self.mouse_lock = threading.Lock()

        self.mouse_buttons = bytearray(2)  # 2字节存储按键状态

        # ===== 新增: 灵敏度 =====
        from core.config import Config
        self.sensitivity = Config.DEFAULT_SENSITIVITY

        # 键盘编码器
        self.keyboard_encoder = KeyboardEncoder()
        self.keyboard_encoder.on_f5_pressed = self.toggle_state

        # 统计
        self.packet_seq = 0
        self.total_packets_sent = 0
        self.actual_rate = 0.0

    def start(self, server_ip: str, tcp_port: int):
        """
        启动控制发送器

        Args:
            server_ip: 服务器IP
            tcp_port: TCP端口 (控制端口 = TCP + 3)
        """
        if self.is_running:
            return

        self.server_ip = server_ip
        self.control_port = tcp_port + 3

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.is_running = True

            # 启动键盘监听
            self.keyboard_encoder.start()
            # 添加状态变化回调
            self.keyboard_encoder.on_state_change = self._on_state_change_callback

            # 启动发送线程
            self.send_thread = threading.Thread(target=self._send_loop, daemon=True)
            self.send_thread.start()

            print(f"[ControlSender] 已启动 -> {server_ip}:{self.control_port}")
            print(f"[ControlSender] 目标频率: {self.target_rate} Hz")
        except Exception as e:
            print(f"[ControlSender] 启动失败: {e}")

    def stop(self):
        """停止控制发送器"""
        self.is_running = False
        self.keyboard_encoder.stop()

        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        print("[ControlSender] 已停止")

    # 在第 84 行 stop() 方法后添加新方法
    def _on_state_change_callback(self, new_state):
        """状态变化回调,通知事件总线"""
        if hasattr(self, 'event_bus'):
            from utils.events import Events
            self.event_bus.publish(Events.CONTROL_STATE_CHANGED, new_state)

    def toggle_state(self):
        """切换 Ready/Not Ready 状态"""
        self.state = 1 - self.state
        state_str = "Ready" if self.state == 1 else "Not Ready"
        print(f"[ControlSender] 状态切换 -> {state_str}")

        # 触发回调
        if hasattr(self, '_on_state_change_callback'):
            self._on_state_change_callback(self.state)

        return self.state

    def update_mouse_position(self, dx: int, dy: int, dt: float):
        """
        更新鼠标位置并计算速度

        Args:
            x: 鼠标X坐标
            y: 鼠标Y坐标
            dt: 时间间隔 (秒)
        """
        with self.mouse_lock:
            if dt > 0:
                # 计算原始速度
                raw_vx = dx / dt
                raw_vy = dy / dt

                # ===== 新增: 应用灵敏度和缩放因子 =====
                from core.config import Config

                # 应用灵敏度和缩放
                self.mouse_velocity_x = raw_vx * self.sensitivity * Config.MOUSE_SCALE_FACTOR
                self.mouse_velocity_y = raw_vy * self.sensitivity * Config.MOUSE_SCALE_FACTOR

                # 限幅
                self.mouse_velocity_x = max(Config.MIN_MOUSE_VELOCITY,
                                            min(Config.MAX_MOUSE_VELOCITY, self.mouse_velocity_x))
                self.mouse_velocity_y = max(Config.MIN_MOUSE_VELOCITY,
                                            min(Config.MAX_MOUSE_VELOCITY, self.mouse_velocity_y))

            self.last_mouse_dx = dx
            self.last_mouse_dy = dy

    def update_mouse_buttons(self, left: bool, right: bool, middle: bool,
                             mouse4: bool, mouse5: bool, scroll_up: bool, scroll_down: bool):
        """
        更新鼠标按键状态

        Byte 0 (bit 0-7):
          bit 0: 左键
          bit 1: 右键
          bit 2: 中键
          bit 3: Mouse4(侧键后)
          bit 4: Mouse5(侧键前)
          bit 5: 滚轮向上
          bit 6: 滚轮向下
          bit 7: 保留
        """
        with self.mouse_lock:
            self.mouse_buttons[0] = 0
            if left:
                self.mouse_buttons[0] |= (1 << 0)
            if right:
                self.mouse_buttons[0] |= (1 << 1)
            if middle:
                self.mouse_buttons[0] |= (1 << 2)
            if mouse4:
                self.mouse_buttons[0] |= (1 << 3)
            if mouse5:
                self.mouse_buttons[0] |= (1 << 4)
            if scroll_up:
                self.mouse_buttons[0] |= (1 << 5)
            if scroll_down:
                self.mouse_buttons[0] |= (1 << 6)

    def set_sensitivity(self, sensitivity: float):
        """设置鼠标灵敏度"""
        from core.config import Config
        self.sensitivity = max(Config.MIN_SENSITIVITY,
                               min(Config.MAX_SENSITIVITY, sensitivity))
        print(f"[ControlSender] 灵敏度设置为: {self.sensitivity:.2f}")

    def _send_loop(self):
        """发送循环 - 100Hz"""
        last_time = time.perf_counter()
        packet_count = 0
        stats_time = last_time

        while self.is_running:
            try:
                current_time = time.perf_counter()
                dt = current_time - last_time

                # 获取控制数据
                with self.mouse_lock:
                    mouse_vx = self.mouse_velocity_x
                    mouse_vy = self.mouse_velocity_y
                    mouse_buttons = bytes(self.mouse_buttons)  # 新增

                keyboard_state = self.keyboard_encoder.get_state()

                # 编码数据包
                packet = ControlPacket.encode(
                    self.state,
                    mouse_vx,
                    mouse_vy,
                    mouse_buttons,  # 新增
                    keyboard_state,
                    self.packet_seq
                )

                # 发送
                self.socket.sendto(packet, (self.server_ip, self.control_port))

                self.packet_seq += 1
                self.total_packets_sent += 1
                packet_count += 1

                # 统计实际频率 (每秒)
                if current_time - stats_time >= 1.0:
                    self.actual_rate = packet_count / (current_time - stats_time)
                    packet_count = 0
                    stats_time = current_time

                # 控制发送频率
                elapsed = time.perf_counter() - current_time
                sleep_time = self.send_interval - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

                last_time = current_time

            except Exception as e:
                if self.is_running:
                    print(f"[ControlSender] 发送错误: {e}")

    def get_statistics(self) -> dict:
        """获取统计信息"""
        return {
            'state': 'Ready' if self.state == 1 else 'Not Ready',
            'total_packets': self.total_packets_sent,
            'actual_rate': self.actual_rate,
            'target_rate': self.target_rate,
            'pressed_keys': self.keyboard_encoder.get_pressed_count()
        }