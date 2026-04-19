"""
UDP Socket 基础收发
"""

import socket
import threading
from typing import Optional, Tuple, Callable
import logging


logger = logging.getLogger(__name__)


class UDPSocket:
    """UDP Socket 封装"""

    def __init__(self, local_port: int = 0, timeout: float = 0.1):
        """
        初始化 UDP Socket

        Args:
            local_port: 本地绑定端口（0 表示自动分配）
            timeout: 接收超时时间（秒）
        """
        self.local_port = local_port
        self.timeout = timeout
        self.socket: Optional[socket.socket] = None
        self.is_running = False

    def bind(self) -> int:
        """
        绑定 Socket

        Returns:
            实际绑定的端口号
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('0.0.0.0', self.local_port))
            self.socket.settimeout(self.timeout)

            # 获取实际绑定的端口
            actual_port = self.socket.getsockname()[1]
            logger.info(f"UDP Socket 绑定到端口 {actual_port}")
            return actual_port
        except Exception as e:
            logger.error(f"绑定 UDP Socket 失败: {e}")
            raise

    def send(self, data: bytes, address: Tuple[str, int]) -> int:
        """
        发送数据

        Args:
            data: 数据字节
            address: 目标地址 (IP, port)

        Returns:
            发送的字节数
        """
        if self.socket is None:
            raise RuntimeError("Socket 未绑定")

        try:
            return self.socket.sendto(data, address)
        except Exception as e:
            logger.error(f"发送数据失败: {e}")
            raise

    def recv(self, buffer_size: int = 4096) -> Optional[Tuple[bytes, Tuple[str, int]]]:
        """
        接收数据（非阻塞）

        Args:
            buffer_size: 接收缓冲区大小

        Returns:
            (数据, (源IP, 源端口)) 或 None（超时）
        """
        if self.socket is None:
            raise RuntimeError("Socket 未绑定")

        try:
            data, address = self.socket.recvfrom(buffer_size)
            return data, address
        except socket.timeout:
            return None
        except Exception as e:
            logger.error(f"接收数据失败: {e}")
            raise

    def close(self):
        """关闭 Socket"""
        if self.socket:
            try:
                self.socket.close()
                logger.info("UDP Socket 已关闭")
            except Exception as e:
                logger.error(f"关闭 Socket 失败: {e}")
            finally:
                self.socket = None


class UDPReceiver(threading.Thread):
    """UDP 接收线程"""

    def __init__(
        self,
        local_port: int = 0,
        on_receive: Optional[Callable[[bytes, Tuple[str, int]], None]] = None,
        buffer_size: int = 4096,
        timeout: float = 0.1
    ):
        """
        初始化 UDP 接收线程

        Args:
            local_port: 本地绑定端口
            on_receive: 接收回调函数 (data, address) -> None
            buffer_size: 接收缓冲区大小
            timeout: 接收超时时间
        """
        super().__init__(daemon=True)
        self.udp_socket = UDPSocket(local_port, timeout)
        self.on_receive = on_receive
        self.buffer_size = buffer_size
        self.is_running = False
        self.local_port = 0

    def run(self):
        """接收线程主循环"""
        try:
            # 绑定 Socket
            self.local_port = self.udp_socket.bind()
            self.is_running = True

            logger.info("UDP 接收线程已启动")

            while self.is_running:
                result = self.udp_socket.recv(self.buffer_size)
                if result:
                    data, address = result
                    if self.on_receive:
                        try:
                            self.on_receive(data, address)
                        except Exception as e:
                            logger.error(f"处理接收数据失败: {e}")

        except Exception as e:
            logger.error(f"UDP 接收线程异常: {e}")
        finally:
            self.is_running = False
            self.udp_socket.close()
            logger.info("UDP 接收线程已停止")

    def stop(self):
        """停止接收线程"""
        self.is_running = False
        self.join(timeout=1.0)


class UDPSender:
    """UDP 发送器"""

    def __init__(self, timeout: float = 0.1):
        """
        初始化 UDP 发送器

        Args:
            timeout: 发送超时时间
        """
        self.udp_socket = UDPSocket(timeout=timeout)
        self.local_port = 0

    def bind(self) -> int:
        """
        绑定 Socket

        Returns:
            实际绑定的端口号
        """
        self.local_port = self.udp_socket.bind()
        return self.local_port

    def send(self, data: bytes, address: Tuple[str, int]) -> int:
        """
        发送数据

        Args:
            data: 数据字节
            address: 目标地址 (IP, port)

        Returns:
            发送的字节数
        """
        return self.udp_socket.send(data, address)

    def close(self):
        """关闭 Socket"""
        self.udp_socket.close()
