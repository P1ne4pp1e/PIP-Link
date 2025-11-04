import socket
import threading
from typing import Callable, Optional


class TCPConnection:
    """TCP连接管理类,用于与服务端握手"""

    def __init__(self, timeout: int = 5):
        """
        初始化TCP连接管理器

        Args:
            timeout: 连接超时时间(秒)
        """
        self.socket = None
        self.timeout = timeout
        self.is_connected = False

        # 回调函数
        self.on_connecting: Optional[Callable] = None  # 开始连接时
        self.on_success: Optional[Callable] = None  # 连接成功时
        self.on_timeout: Optional[Callable] = None  # 连接超时时
        self.on_refused: Optional[Callable] = None  # 连接被拒绝时
        self.on_error: Optional[Callable[[Exception], None]] = None  # 其他错误时

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
            if self.on_connecting:
                self.on_connecting()

            # 创建TCP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)

            # 尝试连接
            print(f"[TCP] Attempting handshake to {ip}:{port}")
            self.socket.connect((ip, port))

            # 连接成功
            print(f"[TCP] Handshake successful! Server now knows our IP")

            # 可选: 发送握手消息
            # self.socket.send(b"CLIENT_HANDSHAKE")

            # 等待服务端可能的响应
            self.socket.settimeout(1)
            try:
                response = self.socket.recv(1024)
                if response:
                    print(f"[TCP] Server response: {response.decode('utf-8', errors='ignore')}")
            except socket.timeout:
                pass

            # 关闭TCP连接
            self.close()

            # 标记为已连接(握手成功)
            self.is_connected = True

            # 触发成功回调
            if self.on_success:
                self.on_success()

            print("[TCP] Handshake completed, ready for UDP communication")

        except socket.timeout:
            print(f"[TCP] Connection timeout after {self.timeout}s")
            if self.on_timeout:
                self.on_timeout()
            self.cleanup()

        except ConnectionRefusedError:
            print("[TCP] Connection refused - server not listening")
            if self.on_refused:
                self.on_refused()
            self.cleanup()

        except Exception as e:
            print(f"[TCP] Connection error: {e}")
            if self.on_error:
                self.on_error(e)
            self.cleanup()

    def close(self):
        """关闭TCP连接"""
        if self.socket:
            try:
                self.socket.close()
                print("[TCP] Socket closed")
            except Exception as e:
                print(f"[TCP] Error closing socket: {e}")
            finally:
                self.socket = None

    def cleanup(self):
        """清理连接资源"""
        self.is_connected = False
        self.close()

    def disconnect(self):
        """断开连接"""
        print("[TCP] Disconnecting...")
        self.cleanup()