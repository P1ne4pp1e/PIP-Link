import socket
import threading
import time
from typing import Callable, Optional
from datetime import datetime


class TCPConnection:
    """TCP连接管理类,用于与服务端握手"""

    # 连接状态常量
    STATE_DISCONNECTED = 0
    STATE_CONNECTING = 1
    STATE_CONNECTED = 2
    STATE_ERROR = 3

    def __init__(self, timeout: int = 5):
        """
        初始化TCP连接管理器

        Args:
            timeout: 连接超时时间(秒)
        """
        self.socket = None
        self.timeout = timeout
        self.is_connected = False
        self.keep_alive_thread = None
        self.health_check_thread = None

        # 连接状态
        self.connection_state = self.STATE_DISCONNECTED
        self.connected_time: Optional[datetime] = None
        self.connection_duration = 0  # 秒

        # 心跳和健康检查
        self.last_heartbeat = time.time()
        self.heartbeat_interval = 5  # 秒
        self.heartbeat_timeout = 10  # 秒

        # 回调函数
        self.on_connecting: Optional[Callable] = None  # 开始连接时
        self.on_success: Optional[Callable] = None  # 连接成功时
        self.on_timeout: Optional[Callable] = None  # 连接超时时
        self.on_refused: Optional[Callable] = None  # 连接被拒绝时
        self.on_error: Optional[Callable[[Exception], None]] = None  # 其他错误时
        self.on_disconnected: Optional[Callable] = None  # 连接断开时

    def handshake(self, ip: str, port: int, async_mode: bool = True):
        """
        向目标主机发起TCP握手

        Args:
            ip: 目标IP地址
            port: 目标端口号
            async_mode: 是否异步执行(True为在新线程中执行,False为阻塞执行)
        """
        if async_mode:
            threading.Thread(target=self._do_handshake, args=(ip, port), daemon=True).start()
        else:
            self._do_handshake(ip, port)

    def _do_handshake(self, ip: str, port: int):
        """
        执行实际的TCP握手操作

        Args:
            ip: 目标IP地址
            port: 目标端口号
        """
        try:
            # 触发连接中回调
            self.connection_state = self.STATE_CONNECTING
            if self.on_connecting:
                self.on_connecting()

            # 创建TCP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.settimeout(self.timeout)

            # 尝试连接
            print(f"[TCP] 尝试握手 {ip}:{port}")
            self.socket.connect((ip, port))

            # 连接成功
            print(f"[TCP] 握手成功! 连接到 {ip}:{port}")
            self.connected_time = datetime.now()
            self.last_heartbeat = time.time()

            # 发送 UDP 端口信息给服务器
            if hasattr(self, 'udp_port'):
                try:
                    message = f"UDP_PORT:{self.udp_port}"
                    self.socket.send(message.encode('utf-8'))
                    print(f"[TCP] 已发送 UDP 端口: {self.udp_port}")
                except Exception as e:
                    print(f"[TCP] 发送 UDP 端口失败: {e}")
            else:
                print("[TCP] 未设置 UDP 端口")

            # 尝试接收服务器响应
            self.socket.settimeout(1)
            try:
                response = self.socket.recv(1024)
                if response:
                    print(f"[TCP] 服务器响应: {response.decode('utf-8', errors='ignore')}")
            except socket.timeout:
                pass

            # 保持连接并启动心跳线程
            self.is_connected = True
            self.connection_state = self.STATE_CONNECTED
            print("[TCP] 连接已建立，保持活跃状态")

            # 触发成功回调
            if self.on_success:
                self.on_success()

            # 启动心跳和健康检查线程
            self._start_keep_alive()
            self._start_health_check()

        except socket.timeout:
            print(f"[TCP] 连接超时 ({self.timeout}秒)")
            self.connection_state = self.STATE_ERROR
            if self.on_timeout:
                self.on_timeout()
            self.cleanup()

        except ConnectionRefusedError:
            print("[TCP] 连接被拒绝 - 服务器未监听")
            self.connection_state = self.STATE_ERROR
            if self.on_refused:
                self.on_refused()
            self.cleanup()

        except Exception as e:
            print(f"[TCP] 连接错误: {e}")
            self.connection_state = self.STATE_ERROR
            if self.on_error:
                self.on_error(e)
            self.cleanup()

    def _start_keep_alive(self):
        """启动心跳线程，保持连接活跃"""
        def keep_alive():
            while self.is_connected and self.socket:
                try:
                    # 每 heartbeat_interval 秒发送一个心跳包
                    time.sleep(self.heartbeat_interval)
                    if self.is_connected and self.socket:
                        self.socket.send(b'\x00')
                        self.last_heartbeat = time.time()
                except:
                    break

        if not self.keep_alive_thread or not self.keep_alive_thread.is_alive():
            self.keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
            self.keep_alive_thread.start()

    def _start_health_check(self):
        """启动健康检查线程，定期检测连接状态"""
        def health_check():
            while self.is_connected:
                try:
                    time.sleep(2)  # 每 2 秒检查一次

                    if not self.is_connected:
                        break

                    # 检查心跳超时
                    time_since_heartbeat = time.time() - self.last_heartbeat
                    if time_since_heartbeat > self.heartbeat_timeout:
                        print(f"[TCP] 心跳超时 ({time_since_heartbeat:.1f}s) - 连接可能已断开")
                        self.is_connected = False
                        self.connection_state = self.STATE_DISCONNECTED
                        if self.on_disconnected:
                            self.on_disconnected()
                        break

                except Exception as e:
                    print(f"[TCP] 健康检查错误: {e}")
                    break

        if not self.health_check_thread or not self.health_check_thread.is_alive():
            self.health_check_thread = threading.Thread(target=health_check, daemon=True)
            self.health_check_thread.start()

    def get_connection_duration(self) -> int:
        """获取连接持续时间（秒）"""
        if self.is_connected and self.connected_time:
            return int((datetime.now() - self.connected_time).total_seconds())
        return 0

    def get_connection_time_str(self) -> str:
        """获取格式化的连接时长字符串"""
        duration = self.get_connection_duration()
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    def get_state_str(self) -> str:
        """获取连接状态字符串"""
        states = {
            self.STATE_DISCONNECTED: "Disconnected",
            self.STATE_CONNECTING: "Connecting",
            self.STATE_CONNECTED: "Connected",
            self.STATE_ERROR: "Error"
        }
        return states.get(self.connection_state, "Unknown")

    def close(self):
        """关闭TCP连接"""
        if self.socket:
            try:
                self.socket.close()
                print("[TCP] Socket 已关闭")
            except Exception as e:
                print(f"[TCP] 关闭 Socket 错误: {e}")
            finally:
                self.socket = None

    def cleanup(self):
        """清理连接资源"""
        self.is_connected = False
        self.connection_state = self.STATE_DISCONNECTED
        self.connected_time = None
        self.close()

    def disconnect(self):
        """断开连接"""
        print("[TCP] 正在断开连接...")
        self.is_connected = False
        self.connection_state = self.STATE_DISCONNECTED
        self.cleanup()
        if self.on_disconnected:
            self.on_disconnected()